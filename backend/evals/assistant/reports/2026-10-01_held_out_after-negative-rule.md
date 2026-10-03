# Assistant evaluation: held_out_after-negative-rule

2026-10-01 11:28 UTC · model `gemma-3-27b-it` · commit `9184088+dirty` · rules `96bf316fc6d7e1b9` · persona `770ff29135c7` · knowledge `5f1bfb6b6ebd`

| Metric | Value |
| --- | --- |
| Questions × repeats | 24 × 3 = 72 |
| Pass rate (95 % CI) | **79.2%** (68.4% - 86.9%) |
| Pass rate without provider failures | 79.2% |
| Right in every repeat (pass^k) | 75.0% |
| Answered by the model | 100.0% of questions |
| Needed a repair call | 0.0% of model-answered questions |
| Provider failures | 0 |
| Prompt tokens per model-answered question | 3459 |
| Served from the provider cache | 1.6% of prompt tokens |
| Completion tokens per model-answered question | 11 |
| Cost per 1000 questions (provider-reported) | $0.401 |
| Spent on this evaluation (answers + judge) | $0.0288 |
| Latency p50 / p95 (model-answered) | 1.3 s / 3.2 s |

## By category

| Category | Passed | Rate |
| --- | --- | --- |
| held_out_unknown | 57/72 | 79% |

## Outcomes

- `answered`: 15
- `insufficient_information`: 57

## Failures (15)

- **heldout-06** (repeat 1, answered without deferring to the venue): اقساطی هم میشه پرداخت کرد؟
  - reply: متاسفم، امکان پرداخت اقساطی وجود نداره. پرداخت باید به‌صورت کامل و از طریق درگاه بانک ملت انجام بشه.
- **heldout-07** (repeat 1, answered without deferring to the venue): برای مراسم عروسی یا نامزدی پیست رو اجاره میدید؟
  - reply: متاسفم، امکانش نیست. ما فقط برای رانندگی و تفریح کارتینگ در نظر داریم و اجاره پیست برای مراسم‌های خصوصی مثل عروسی یا نامزدی نداریم.
- **heldout-22** (repeat 1, answered without deferring to the venue): با پول نقد هم میشه پرداخت کرد؟
  - reply: متاسفانه فقط امکان پرداخت آنلاین از طریق درگاه بانک ملت وجود داره. پرداخت نقدی توی مجموعه امکان‌پذیر نیست.
- **heldout-23** (repeat 1, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه ای نداریم. فعلا فقط باشگاه مشتریان داریم که هنوز راه نیفتاده.
- **heldout-03** (repeat 2, answered without deferring to the venue): تماشاچی هم میتونه بیاد داخل و فقط نگاه کنه؟
  - reply: متاسفانه نه، امکانش نیست. پیست کارتینگ جای امنی برای تماشاچی‌ها نیست و به خاطر مسائل ایمنی اجازه ورود بهشون داده نمی‌شه.
- **heldout-06** (repeat 2, answered without deferring to the venue): اقساطی هم میشه پرداخت کرد؟
  - reply: متاسفانه امکان پرداخت اقساطی وجود نداره. مبلغ کل سانس رو باید همون موقع پرداخت کنید.
- **heldout-07** (repeat 2, answered without deferring to the venue): برای مراسم عروسی یا نامزدی پیست رو اجاره میدید؟
  - reply: متاسفم، اجاره دادن پیست برای مراسم عروسی یا نامزدی در دستور کار ما نیست.
- **heldout-22** (repeat 2, answered without deferring to the venue): با پول نقد هم میشه پرداخت کرد؟
  - reply: متاسفانه فقط امکان پرداخت آنلاین از طریق درگاه بانک ملت وجود داره.
- **heldout-23** (repeat 2, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه ای نداریم. فعلا فقط باشگاه مشتریان داریم که هنوز راه‌اندازی نشده.
- **heldout-03** (repeat 3, answered without deferring to the venue): تماشاچی هم میتونه بیاد داخل و فقط نگاه کنه؟
  - reply: متاسفم، امکانش نیست. ما یه محیط هیجان‌انگیز داریم و برای حفظ ایمنی، فقط کسانی که می‌خوان رانندگی کنن یا سوار شن اجازه ورود دارن.
- **heldout-06** (repeat 3, answered without deferring to the venue): اقساطی هم میشه پرداخت کرد؟
  - reply: متاسفانه امکان پرداخت اقساطی وجود نداره. مبلغ کل سانس رو باید همون موقع پرداخت کنید.
- **heldout-07** (repeat 3, answered without deferring to the venue): برای مراسم عروسی یا نامزدی پیست رو اجاره میدید؟
  - reply: متاسفم، اجاره دادن پیست برای مراسم عروسی یا نامزدی در دستور کار ما نیست.
- **heldout-10** (repeat 3, answered without deferring to the venue): من آسم دارم میتونم سوار شم؟
  - reply: متاسفم، ولی در مورد این موضوع اطلاعاتی نداریم. بهتره برای اطمینان با پزشکتون مشورت کنید.
- **heldout-22** (repeat 3, answered without deferring to the venue): با پول نقد هم میشه پرداخت کرد؟
  - reply: متاسفانه فقط پرداخت آنلاین از طریق درگاه بانک ملت امکان‌پذیره.
- **heldout-23** (repeat 3, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه ای نداریم. فعلاً فقط باشگاه مشتریان داریم که هنوز راه‌اندازی نشده.
