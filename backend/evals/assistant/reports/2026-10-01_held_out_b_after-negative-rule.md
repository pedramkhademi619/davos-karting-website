# Assistant evaluation: held_out_b_after-negative-rule

2026-10-01 11:28 UTC · model `gemma-3-27b-it` · commit `9184088+dirty` · rules `96bf316fc6d7e1b9` · persona `770ff29135c7` · knowledge `5f1bfb6b6ebd`

| Metric | Value |
| --- | --- |
| Questions × repeats | 12 × 3 = 36 |
| Pass rate (95 % CI) | **30.6%** (18.0% - 46.9%) |
| Pass rate without provider failures | 30.6% |
| Right in every repeat (pass^k) | 25.0% |
| Answered by the model | 100.0% of questions |
| Needed a repair call | 0.0% of model-answered questions |
| Provider failures | 0 |
| Prompt tokens per model-answered question | 3460 |
| Served from the provider cache | 0.0% of prompt tokens |
| Completion tokens per model-answered question | 33 |
| Cost per 1000 questions (provider-reported) | $0.414 |
| Spent on this evaluation (answers + judge) | $0.0149 |
| Latency p50 / p95 (model-answered) | 2.3 s / 3.7 s |

## By category

| Category | Passed | Rate |
| --- | --- | --- |
| held_out_unknown_b | 11/36 | 31% |

## Outcomes

- `answered`: 27
- `insufficient_information`: 9

## Failures (25)

- **heldoutb-01** (repeat 1, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، نداریم. کودک زیر ۴ سال به هیچ عنوان نمی‌تونه سوار هیچ خودرویی بشه، نه به عنوان راننده و نه روی صندلی عقب.
- **heldoutb-04** (repeat 1, answered without deferring to the venue): روزهای برفی یا بارونی هم کار میکنید؟
  - reply: متاسفانه در روزهای برفی یا بارونی پیست تعطیل هست. ایمنی مهم‌تر از همه چیزه و رانندگی توی این شرایط خطرناکه.
- **heldoutb-05** (repeat 1, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 1, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! ما سیستمی برای ثبت و نمایش رکوردهای دور نداریم.
- **heldoutb-07** (repeat 1, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال. این سن برای نشستن روی صندلی عقب خودرو دونفره است.
- **heldoutb-09** (repeat 1, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مهم نیست، مهم اینه که چندتا بچه ۴ تا ۱۵ ساله دارید یا نه. چون ممکنه لازم باشه سانس‌ها رو تقسیم کنیم.
- **heldoutb-10** (repeat 1, answered without deferring to the venue): میتونم به جای خودم یکی دیگه رو بفرستم؟
  - reply: متاسفم، امکانش نیست! رزرو اسمی است و فقط کسی که با مشخصات خودش رزرو کرده می‌تونه سوار بشه. این برای حفظ ایمنی و جلوگیری از سوءاستفاده‌ست.
- **heldoutb-12** (repeat 1, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رانندگی با خودرو تک‌نفره، فقط باید سن و قدتون با شرایطی که گفتم مطابقت داشته باشه. برای خودرو دونفره هم راننده باید گواهینامه داشته باشه.
- **heldoutb-01** (repeat 2, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، نداریم. کودک زیر ۴ سال به هیچ عنوان نمی‌تونه سوار هیچ خودرویی بشه، نه به عنوان راننده و نه روی صندلی عقب.
- **heldoutb-04** (repeat 2, answered without deferring to the venue): روزهای برفی یا بارونی هم کار میکنید؟
  - reply: متاسفانه در روزهای برفی یا بارونی پیست تعطیل هست. ایمنی مهم‌تر از هر چیزیه و رانندگی توی این شرایط خطرناکه.
- **heldoutb-05** (repeat 2, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 2, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! ما سیستمی برای ثبت و نمایش رکوردهای دور نداریم.
- **heldoutb-07** (repeat 2, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال. این سن برای نشستن روی صندلی عقب خودرو دونفره است. البته اگر کودک زیر ۴ سال باشه، اصلاً نمی‌تونه سوار هیچ خودرویی بشه.
- **heldoutb-09** (repeat 2, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مهم نیست، مهم اینه که چندتا بچه ۴ تا ۱۵ ساله دارید یا نه. چون ممکنه لازم باشه سانس‌ها رو تقسیم کنیم.
- **heldoutb-10** (repeat 2, answered without deferring to the venue): میتونم به جای خودم یکی دیگه رو بفرستم؟
  - reply: متاسفم، امکانش نیست! رزرو اسمی است و فقط کسی که با مشخصات خودش رزرو کرده می‌تونه سوار بشه. این برای حفظ امنیت و جلوگیری از مشکلات احتمالیه.
- **heldoutb-12** (repeat 2, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رانندگی با خودرو تک‌نفره، فقط باید شرایط سنی و قد رو داشته باشید. برای خودرو دونفره هم راننده باید گواهینامه داشته باشه.
- **heldoutb-01** (repeat 3, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، نداریم. کودک زیر ۴ سال به هیچ عنوان نمی‌تونه سوار هیچ خودرویی بشه، نه به عنوان راننده و نه روی صندلی عقب.
- **heldoutb-02** (repeat 3, answered without deferring to the venue): بلیط یا کارت هدیه میفروشید؟
  - reply: متاسفانه نه، فعلاً بلیط یا کارت هدیه نداریم.
- **heldoutb-04** (repeat 3, answered without deferring to the venue): روزهای برفی یا بارونی هم کار میکنید؟
  - reply: متاسفانه در روزهای برفی یا بارونی پیست تعطیل است. ایمنی مهم‌تر از هر چیزیه!
- **heldoutb-05** (repeat 3, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 3, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست. هیچ اطلاعاتی درباره رکورد دورها توی این متن‌ها نیست.
- **heldoutb-07** (repeat 3, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال! این سن برای نشستن روی صندلی عقب خودرو دونفره است، به شرطی که یه بزرگسال گواهینامه‌دار هم راننده باشه. البته اگه سنش زیر ۴ سال باشه، اصلاً نمی‌تونه سوار هیچ خودرویی بشه.
- **heldoutb-09** (repeat 3, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مهم نیست، مهم اینه که چندتا بچه ۴ تا ۱۵ ساله دارید یا نه. چون ممکنه لازم باشه سانس‌ها رو تقسیم کنیم.
- **heldoutb-10** (repeat 3, answered without deferring to the venue): میتونم به جای خودم یکی دیگه رو بفرستم؟
  - reply: متاسفم، امکانش نیست! رزرو اسمی است و فقط کسی که با مشخصات خودش رزرو کرده می‌تونه سوار بشه. این برای حفظ امنیت و جلوگیری از مشکلات احتمالیه.
- **heldoutb-12** (repeat 3, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رانندگی با خودرو تک‌نفره، فقط باید سن و قدتون با شرایطی که گفتم مطابقت داشته باشه. برای خودرو دونفره هم راننده باید گواهینامه داشته باشه.
