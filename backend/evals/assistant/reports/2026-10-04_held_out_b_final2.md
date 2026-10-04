# Assistant evaluation: held_out_b_final2

2026-10-04 18:55 UTC · model `gemma-3-27b-it` · commit `88c5d57+dirty` · rules `96bf316fc6d7e1b9` · persona `770ff29135c7` · knowledge `5f1bfb6b6ebd`

| Metric | Value |
| --- | --- |
| Questions × repeats | 12 × 3 = 36 |
| Pass rate (95 % CI) | **55.6%** (39.6% - 70.5%) |
| Pass rate without provider failures | 55.6% |
| Right in every repeat (pass^k) | 41.7% |
| Answered by the model | 100.0% of questions |
| Needed a repair call | 75.0% of model-answered questions |
| Provider failures | 0 |
| Prompt tokens per model-answered question | 4021 |
| Served from the provider cache | 54.4% of prompt tokens |
| Completion tokens per model-answered question | 36 |
| Cost per 1000 questions (provider-reported) | $0.274 |
| Spent on this evaluation (answers + judge) | $0.0099 |
| Latency p50 / p95 (model-answered) | 2.9 s / 13.0 s |

## By category

| Category | Passed | Rate |
| --- | --- | --- |
| held_out_unknown_b | 20/36 | 56% |

## Outcomes

- `answered`: 18
- `insufficient_information`: 18

## Failures (16)

- **heldoutb-05** (repeat 1, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 1, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! اطلاعات مربوط به رکورد دورها در دسترس عموم نیست.
- **heldoutb-07** (repeat 1, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال! این سن برای نشستن روی صندلی عقب خودرو دونفره است، به شرطی که یه بزرگسال گواهینامه داشته باشه که رانندگی کنه. البته اگه کسی زیر ۴ سال باشه، اصلاً نمی‌تونه سوار هیچ ماشینی بشه.
- **heldoutb-09** (repeat 1, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: حداقل تعداد نفرات برای گروه مهم نیست، مهم اینه که چندتا بچه ۴ تا ۱۵ ساله دارید یا نه. چون ممکنه لازم باشه سانس‌ها رو تقسیم کنیم.
- **heldoutb-01** (repeat 2, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، نداریم. کودک زیر ۴ سال به هیچ عنوان نمی‌تونه سوار هیچ خودرویی بشه، نه به عنوان راننده و نه روی صندلی عقب.
- **heldoutb-05** (repeat 2, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-07** (repeat 2, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال! این سن برای نشستن روی صندلی عقب خودرو دونفره است، به شرطی که یه بزرگسال گواهینامه‌دار هم راننده باشه. البته اگه سنش زیر ۴ سال باشه، اصلاً نمی‌تونه سوار بشه.
- **heldoutb-09** (repeat 2, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: متاسفانه حداقل تعداد نفرات برای گروه مشخص نیست. برای اینکه بتونم بهتون کمک کنم، میشه بگید دقیقاً چند نفر هستید و چندتا بچه بین ۴ تا ۱۵ سال دارید؟
- **heldoutb-12** (repeat 2, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رزرو آنلاین فقط شماره موبایل و کد پیامکی لازمه، و برای رانندگی خودرو دونفره راننده باید گواهینامه داشته باشه.
- **heldoutb-01** (repeat 3, answered without deferring to the venue): صندلی ماشین بچه برای نوزاد دارید؟
  - reply: متاسفم، نداریم! کودک زیر ۴ سال به هیچ عنوان نمی‌تونه سوار هیچ خودرویی بشه، نه به عنوان راننده و نه روی صندلی عقب.
- **heldoutb-02** (repeat 3, answered without deferring to the venue): بلیط یا کارت هدیه میفروشید؟
  - reply: متاسفم، فعلاً نه کارت هدیه داریم و نه بلیط. ولی باشگاه مشتریان داوس به زودی راه می‌افته که کلی تخفیف و هدیه داره.
- **heldoutb-05** (repeat 3, answered without deferring to the venue): شماره حساب برای کارت به کارت دارید؟
  - reply: ما شماره حساب برای کارت به کارت نداریم. پرداخت فقط از طریق درگاه بانک ملت در صفحه «رزرو سانس» سایت امکان‌پذیره.
- **heldoutb-06** (repeat 3, answered without deferring to the venue): میشه رکورد دور خودم رو ببینم؟
  - reply: متاسفم، امکانش نیست! ما سیستمی برای ثبت و نمایش رکوردهای دور نداریم.
- **heldoutb-07** (repeat 3, answered without deferring to the venue): سن مجاز برای همراه چنده؟
  - reply: ۴ تا ۱۵ سال می‌تونه روی صندلی عقب خودرو دونفره بشینه، به شرطی که راننده گواهینامه داشته باشه. ولی اگه خودش بخواد رانندگی کنه، باید ۱۱ سال به بالا باشه و قدش بیشتر از ۱۴۰ سانتی‌متر باشه، اونم فقط شنبه تا چهارشنبه از ساعت ۳ تا ۶ بعدازظهر.
- **heldoutb-09** (repeat 3, answered without deferring to the venue): حداقل تعداد نفرات برای گروه چنده؟
  - reply: متاسفانه حداقل تعداد نفرات برای گروه مشخص نیست. برای اینکه بتونم بهت کمک کنم، میشه بگی چند نفر هستید و چندتا بچه بین ۴ تا ۱۵ سال دارید؟
- **heldoutb-12** (repeat 3, answered without deferring to the venue): آیا کارت ملی لازمه؟
  - reply: نه، نیازی به کارت ملی نیست. برای رزرو آنلاین فقط شماره موبایل و کد پیامکی لازمه.
