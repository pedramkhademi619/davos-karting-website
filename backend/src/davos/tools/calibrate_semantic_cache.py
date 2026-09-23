"""Measures the local embedding model on typical questions and checks that the cache would treat them correctly.

    docker compose exec api python -m davos.tools.calibrate_semantic_cache

Runs entirely on this machine (the model is a local folder). It prints the cosine similarity of

* paraphrases: different words, same meaning, must be served from the cache;
* contrast pairs: look alike, have different answers (another weekday, 140 vs 135 cm, "can" vs "cannot"), must NOT be;
* unrelated pairs, must NOT be;

and what the signature guard does with each. It exits with 1 when any contrast or unrelated pair would be served
from the cache at the configured threshold, so it can be re-run after changing the model, the threshold or the
discriminator vocabulary. The pairs below are about Davos Karting; add your own real questions to them.
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from collections.abc import Sequence

from davos.modules.assistant.adapters.embedding.sentence_transformer_embedding import SentenceTransformerEmbedding
from davos.modules.assistant.domain.services.query_signature_builder import QuerySignatureBuilder
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.platform.settings.app_settings import AppSettings

Pair = tuple[str, str]

PARAPHRASES: tuple[Pair, ...] = (
    ("ساعت کاری شما چیه؟", "شما چه ساعتی باز هستید؟"),
    ("ساعت کاری شما چیه؟", "چه ساعت‌هایی کار می‌کنید؟"),
    ("چطور رزرو کنم؟", "روش رزرو نوبت چیه؟"),
    ("چطور نوبت رزرو کنم؟", "برای گرفتن نوبت چیکار باید بکنم؟"),
    ("شماره رزرو چنده؟", "برای رزرو به چه شماره‌ای زنگ بزنم؟"),
    ("هر سانس چند نفر ظرفیت داره؟", "ظرفیت هر سانس چقدره؟"),
    ("باشگاه مشتریان چیه؟", "باشگاه مشتریان داوس یعنی چی؟"),
    ("How do I book a session?", "What is the way to make a reservation?"),
    ("What are your opening hours?", "When are you open?"),
    ("ما هي ساعات العمل؟", "متى تفتحون؟"),
    ("ساعت کاری شما چیه؟", "What are your opening hours?"),
)
# The same question worded a little differently: what repeat traffic really looks like.
VARIANTS: tuple[Pair, ...] = (
    ("ساعت کاری شما چیه؟", "ساعت کاری چیه؟"),
    ("ساعت کاری شما چیه؟", "ساعت کاری شما چیست؟"),
    ("ساعت کاری شما چیه؟", "سلام ساعت کاری شما چیه؟"),
    ("ساعت کاری شما چیه؟", "ساعت کاری؟"),
    ("چطور رزرو کنم؟", "چطوری رزرو کنم؟"),
    ("چطور رزرو کنم؟", "لطفا بگید چطور رزرو کنم"),
    ("شماره رزرو چنده؟", "شماره رزرو چند است؟"),
    ("قیمت ماشین چقدره؟", "قیمت ماشین چقدر است؟"),
    ("باشگاه مشتریان چیه؟", "باشگاه مشتریان چیست؟"),
    ("هر سانس چند نفر ظرفیت داره؟", "هر سانس چند نفر ظرفیت دارد؟"),
    ("What are your opening hours?", "what are your opening hours"),
    ("What are your opening hours?", "What are your opening hours please?"),
)
CONTRASTS: tuple[Pair, ...] = (
    ("ساعت کاری پنجشنبه چیه؟", "ساعت کاری شنبه چیه؟"),
    ("ساعت کاری پنجشنبه چیه؟", "ساعت کاری جمعه چیه؟"),
    ("دخترم ۱۲ ساله است و قدش ۱۴۰ است، می‌تواند رانندگی کند؟", "دخترم ۱۲ ساله است و قدش ۱۳۵ است، می‌تواند رانندگی کند؟"),
    ("پسرم ۱۰ ساله است، می‌تواند رانندگی کند؟", "پسرم ۱۶ ساله است، می‌تواند رانندگی کند؟"),
    ("قیمت ماشین در روز عادی چقدر است؟", "قیمت ماشین در روز تعطیل چقدر است؟"),
    ("قیمت ماشین تک نفره چقدر است؟", "قیمت ماشین دو نفره چقدر است؟"),
    ("می‌توانم پنجشنبه رزرو کنم؟", "نمی‌توانم پنجشنبه رزرو کنم؟"),
    ("Can I book on Thursday?", "Can I book on Friday?"),
    ("مادرم گواهینامه دارد، می‌تواند جلو بنشیند؟", "مادرم گواهینامه ندارد، می‌تواند جلو بنشیند؟"),
)
UNRELATED: tuple[Pair, ...] = (
    ("ساعت کاری شما چیه؟", "باشگاه مشتریان چیه؟"),
    ("ساعت کاری شما چیه؟", "قیمت بیت کوین امروز چنده؟"),
    ("چطور رزرو کنم؟", "آدرس پیست کجاست؟"),
    ("شماره رزرو چنده؟", "لباس مخصوص لازمه؟"),
    ("How do I book a session?", "What is the capital of France?"),
    ("ظرفیت هر سانس چقدره؟", "آب و هوای شیراز چطوره؟"),
)
# What customers ask, three ways each. Two phrasings of one topic should share an answer; phrasings of different
# topics must never, so every cross-topic pair is a chance to catch a threshold that is too low.
TOPICS: dict[str, tuple[str, ...]] = {
    "booking": ("چطور نوبت رزرو کنم؟", "برای رزرو باید چیکار کنم؟", "می‌خوام یه نوبت بگیرم، از کجا شروع کنم؟"),
    "hours": ("ساعت کاری شما چیه؟", "چه ساعتی باز هستید؟", "تا ساعت چند کار می‌کنید؟"),
    "prices": ("قیمت ماشین چقدره؟", "هزینه هر سانس چنده؟", "برای یک نفر چقدر باید پرداخت کنم؟"),
    "capacity": ("هر سانس چند نفر ظرفیت داره؟", "چند نفر می‌تونن با هم سوار بشن؟", "ظرفیت هر نوبت چقدره؟"),
    "club": ("باشگاه مشتریان چیه؟", "عضویت در باشگاه چطوریه؟", "تخفیف دائمی دارید؟"),
    "address": ("آدرس پیست کجاست؟", "پیست کجا هست؟", "چطور به پیست برسم؟"),
    "clothing": ("لباس مخصوص لازمه؟", "با چه لباسی بیام؟", "کفش ورزشی باید بپوشم؟"),
    "two-seater": (
        "شرایط ماشین دو نفره چیه؟",
        "کی می‌تونه ماشین دو نفره رو رانندگی کنه؟",
        "بچه پشت ماشین دو نفره می‌تونه بشینه؟",
    ),
    "single-seater": (
        "ماشین تک نفره برای چه سنی هست؟",
        "محدودیت سنی ماشین تک نفره چیه؟",
        "بچه‌ها می‌تونن تک نفره رانندگی کنن؟",
    ),
    "support": ("چطور با پشتیبانی تماس بگیرم؟", "می‌خوام شکایت کنم", "به کی پیام بدم؟"),
}
_SWEEP = (0.86, 0.88, 0.90, 0.92, 0.94, 0.96)
_LATENCY_SAMPLES = 40


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _peak_memory_mb() -> float | None:
    try:
        with open("/proc/self/status", encoding="ascii") as status:
            for line in status:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) / 1024
    except (OSError, ValueError):
        return None
    return None


async def _run() -> int:
    settings = AppSettings()
    threshold = settings.semantic_cache_similarity_threshold
    normalizer = PersianTextNormalizer()
    signatures = QuerySignatureBuilder(normalizer, settings.semantic_cache_extra_discriminators)
    model = SentenceTransformerEmbedding(
        model_path=settings.embedding_model_path,
        model_name=settings.embedding_model_name,
        dimension=settings.embedding_dimension,
        threads=settings.embedding_threads,
    )
    started = time.perf_counter()
    await model.warm_up()
    if not model.is_ready:
        print(f"the embedding model could not be loaded from {settings.embedding_model_path!r}")
        return 2
    memory = _peak_memory_mb()
    print(
        f"model loaded in {time.perf_counter() - started:.1f} s" + (f"; peak memory {memory:.0f} MB" if memory else "")
    )

    async def vector(text: str) -> tuple[float, ...]:
        return (await model.embed_query(normalizer.normalize(text))).values

    await vector("گرم کردن مدل")
    timings: list[float] = []
    for number in range(_LATENCY_SAMPLES):  # distinct texts, one at a time, so the LRU never answers
        began = time.perf_counter()
        await vector(f"سوال شماره {number} درباره ساعت کاری و رزرو نوبت در پیست کارتینگ")
        timings.append((time.perf_counter() - began) * 1000)
    timings.sort()
    print(
        f"embedding latency per question: median {statistics.median(timings):.0f} ms, "
        f"95th percentile {timings[int(len(timings) * 0.95)]:.0f} ms, worst {timings[-1]:.0f} ms"
    )

    async def measure(title: str, pairs: Sequence[Pair]) -> list[tuple[float, bool]]:
        print(f"\n== {title}")
        rows: list[tuple[float, bool]] = []
        for first, second in pairs:
            similarity = _cosine(await vector(first), await vector(second))
            same_signature = signatures.build(first) == signatures.build(second)
            hit = similarity >= threshold and same_signature
            rows.append((similarity, hit))
            note = "same signature" if same_signature else "signatures DIFFER"
            verdict = "SERVED FROM CACHE" if hit else "goes to the model"
            print(f"  {similarity:.3f}  {note:17}  {verdict:17}  {first}  <->  {second}")
        return rows

    variants = await measure("light variants of one question (should be served from the cache)", VARIANTS)
    paraphrases = await measure("paraphrases, different words (would be nice to serve)", PARAPHRASES)
    contrasts = await measure("contrast pairs (different answers: must go to the model)", CONTRASTS)
    unrelated = await measure("unrelated pairs (must go to the model)", UNRELATED)

    def span(rows: Sequence[tuple[float, bool]]) -> str:
        return f"{min(r[0] for r in rows):.3f} to {max(r[0] for r in rows):.3f}"

    # Topic clusters: every pair of the 30 questions, split into same-topic and different-topic pairs.
    questions = [(topic, text) for topic, texts in TOPICS.items() for text in texts]
    vectors = {text: await vector(text) for _, text in questions}
    within: list[tuple[float, bool, str, str]] = []
    across: list[tuple[float, bool, str, str]] = []
    for index, (topic_a, first) in enumerate(questions):
        for topic_b, second in questions[index + 1 :]:
            entry = (
                _cosine(vectors[first], vectors[second]),
                signatures.build(first) == signatures.build(second),
                first,
                second,
            )
            (within if topic_a == topic_b else across).append(entry)
    print(f"\n== topic clusters: {len(TOPICS)} topics x 3 phrasings")
    print(f"  {len(within)} same-topic pairs and {len(across)} cross-topic pairs")
    print("  closest cross-topic pairs (the ones a too-low threshold would confuse):")
    for similarity, same_signature, first, second in sorted(across, reverse=True)[:6]:
        note = "same signature" if same_signature else "signatures DIFFER"
        print(f"    {similarity:.3f}  {note:17}  {first}  <->  {second}")
    print(
        f"  same-topic similarity  {min(w[0] for w in within):.3f} to {max(w[0] for w in within):.3f}"
        f" (median {statistics.median(w[0] for w in within):.3f})"
    )
    print(
        f"  cross-topic similarity {min(a[0] for a in across):.3f} to {max(a[0] for a in across):.3f}"
        f" (median {statistics.median(a[0] for a in across):.3f})"
    )
    print("\n  threshold sweep (a pair is served when similarity >= threshold AND the signatures match):")
    print("    threshold | wrongly served: cross-topic, contrast+unrelated | served: light variants, same-topic")
    must_not_match = [
        (_cosine(await vector(a), await vector(b)), signatures.build(a) == signatures.build(b))
        for a, b in CONTRASTS + UNRELATED
    ]
    variant_rows = [
        (_cosine(await vector(a), await vector(b)), signatures.build(a) == signatures.build(b)) for a, b in VARIANTS
    ]
    lowest_safe: float | None = None
    for value in _SWEEP:
        wrong_topics = sum(s >= value and same for s, same, _, _ in across)
        wrong_other = sum(s >= value and same for s, same in must_not_match)
        served_variants = sum(s >= value and same for s, same in variant_rows)
        served_topics = sum(s >= value and same for s, same, _, _ in within)
        if lowest_safe is None and wrong_topics == 0 and wrong_other == 0:
            lowest_safe = value
        marker = "  <- configured" if abs(value - threshold) < 1e-9 else ""
        wrong = f"{wrong_topics:>3} of {len(across)}, {wrong_other:>2}"
        served_text = f"{served_variants:>2} of {len(VARIANTS)}, {served_topics:>2} of {len(within)}"
        print(f"    {value:.2f}      | {wrong:<32}| {served_text}{marker}")
    if lowest_safe is None:
        print("  no tested threshold avoids every wrong hit on these questions")
    else:
        print(f"  lowest tested threshold with no wrong hit: {lowest_safe:.2f}")

    unsafe = sum(hit for _, hit in contrasts + unrelated) + sum(s >= threshold and same for s, same, _, _ in across)
    print(f"\n== summary at threshold {threshold}")
    served_now = sum(h for _, h in variants)
    print(f"  light-variant similarity {span(variants)}; served from the cache: {served_now}/{len(variants)}")
    served = sum(h for _, h in paraphrases)
    print(f"  paraphrase similarity {span(paraphrases)}; served from the cache: {served}/{len(paraphrases)}")
    print(
        f"  contrast similarity   {span(contrasts)}; wrongly served: {sum(h for _, h in contrasts)}/{len(contrasts)}"
        f" (on similarity alone {sum(s >= threshold for s, _ in contrasts)}/{len(contrasts)} would be)"
    )
    print(
        f"  unrelated similarity  {span(unrelated)}; wrongly served: {sum(h for _, h in unrelated)}/{len(unrelated)}"
        f" (on similarity alone {sum(s >= threshold for s, _ in unrelated)}/{len(unrelated)} would be)"
    )
    model.close()
    if unsafe:
        print("\nUNSAFE: raise SEMANTIC_CACHE_SIMILARITY_THRESHOLD or extend the discriminator words.")
        return 1
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
