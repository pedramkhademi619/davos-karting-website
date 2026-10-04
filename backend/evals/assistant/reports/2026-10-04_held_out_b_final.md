# Assistant evaluation: held_out_b_final

2026-10-04 18:41 UTC · model `gemma-3-27b-it` · commit `051fd91+dirty` · rules `96bf316fc6d7e1b9` · persona `770ff29135c7` · knowledge `5f1bfb6b6ebd`

| Metric | Value |
| --- | --- |
| Questions × repeats | 12 × 3 = 36 |
| Pass rate (95 % CI) | **55.6%** (39.6% - 70.5%) |
| Pass rate without provider failures | 55.6% |
| Right in every repeat (pass^k) | 50.0% |
| Answered by the model | 100.0% of questions |
| Needed a repair call | 75.0% of model-answered questions |
| Provider failures | 0 |
| Prompt tokens per model-answered question | 4048 |
| Served from the provider cache | 68.7% of prompt tokens |
| Completion tokens per model-answered question | 36 |
| Cost per 1000 questions (provider-reported) | $0.244 |
| Spent on this evaluation (answers + judge) | $0.0088 |
| Latency p50 / p95 (model-answered) | 3.1 s / 4.2 s |

## By category

| Category | Passed | Rate |
| --- | --- | --- |
| held_out_unknown_b | 20/36 | 56% |

## Outcomes

- `answered`: 17
- `insufficient_information`: 19

## Failures (16)

- **heldoutb-01** (repeat 1, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، برای نوزاد صندلی ماشین نداریم. چون حداقل سن برای سوار شدن به هر نوع خودرو ۴ ساله.
- **heldoutb-05** (repeat 1, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 1, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! ما سیستمی برای ثبت و نمایش رکوردهای دور نداریم.
- **heldoutb-07** (repeat 1, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال می‌تونه روی صندلی عقب خودرو دونفره با یه بزرگسال گواهینامه‌دار بشینه. البته اگه خودش بخواد رانندگی کنه، شرایطش فرق داره و به سن و قدش بستگی داره.
- **heldoutb-09** (repeat 1, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مشخص نیست، چون بستگی به این داره که چندتا بچه دارید و می‌خواید با چندتا خودرو دونفره بیاید. اگر فقط تعداد کل نفرات رو بگید، می‌تونم بگم به چندتا سانس نیاز دارید.
- **heldoutb-12** (repeat 1, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رزرو آنلاین فقط شماره موبایل و کد پیامکی لازمه، و برای رانندگی خودرو دونفره راننده باید گواهینامه داشته باشه.
- **heldoutb-01** (repeat 2, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، برای نوزاد صندلی ماشین نداریم. چون حداقل سن برای سوار شدن به هر نوع خودرو ۴ ساله.
- **heldoutb-06** (repeat 2, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! ما سیستمی برای ثبت و نمایش رکوردهای دور نداریم.
- **heldoutb-07** (repeat 2, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال! چون می‌تونه روی صندلی عقب خودرو دونفره با یه بزرگسال گواهینامه‌دار بشینه. البته اگه خودش بخواد رانندگی کنه، شرایط دیگه‌ای داره.
- **heldoutb-09** (repeat 2, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مشخص نیست، چون هم می‌تونید یک نفر رزرو کنید و هم بیشتر. ولی برای اینکه بتونیم دقیقاً بهتون بگم چند سانس لازم دارید، بگید چند نفر هستید و چندتاشون بچه بین ۴ تا ۱۵ سال دارین.
- **heldoutb-01** (repeat 3, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، برای نوزاد صندلی ماشین نداریم. چون حداقل سن برای سوار شدن به هر نوع خودرو ۴ ساله.
- **heldoutb-05** (repeat 3, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 3, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! اطلاعات مربوط به رکورد دورها در دسترس عموم نیست.
- **heldoutb-07** (repeat 3, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال می‌تونه روی صندلی عقب خودرو دونفره با یه بزرگسال گواهینامه‌دار بشینه. البته اگه خودش بخواد رانندگی کنه، باید ۱۱ سال به بالا باشه و قدش بیشتر از ۱۴۰ سانتی‌متر باشه و روزهای شنبه تا چهارشنبه ساعت ۱۵ تا ۱۸ باشه.
- **heldoutb-09** (repeat 3, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مشخص نیست، چون بستگی داره چندتا خودرو لازم داشته باشید. اگر تعداد کل نفرات رو بگید و اینکه بچه ۴ تا ۱۵ ساله دارید یا نه، می‌تونم بگم چندتا سانس لازم دارید.
- **heldoutb-12** (repeat 3, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رزرو آنلاین فقط شماره موبایل و کد پیامکی لازمه، و برای رانندگی خودرو دونفره راننده باید گواهینامه داشته باشه.
