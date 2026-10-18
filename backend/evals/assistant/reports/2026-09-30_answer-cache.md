# Answer cache evaluation

2026-09-30 · embedding model `paraphrase-multilingual-MiniLM-L12-v2-int8` · 25 paraphrase pairs, 20 look-alike pairs, 6 uncacheable pairs

**Recommended threshold: 0.94** (lowest with no false hit and a 0.02 margin above the strongest look-alike that passes both rules: 0.912).

| Threshold | Paraphrases answered from the cache | False hits (look-alikes served) |
| --- | --- | --- |
| 0.50 | 16/25 | 11/20 |
| 0.52 | 16/25 | 10/20 |
| 0.54 | 16/25 | 9/20 |
| 0.56 | 15/25 | 8/20 |
| 0.58 | 15/25 | 8/20 |
| 0.60 | 13/25 | 8/20 |
| 0.62 | 13/25 | 8/20 |
| 0.64 | 13/25 | 8/20 |
| 0.66 | 11/25 | 8/20 |
| 0.68 | 10/25 | 8/20 |
| 0.70 | 9/25 | 8/20 |
| 0.72 | 8/25 | 7/20 |
| 0.74 | 8/25 | 7/20 |
| 0.76 | 8/25 | 5/20 |
| 0.78 | 5/25 | 4/20 |
| 0.80 | 4/25 | 3/20 |
| 0.82 | 4/25 | 3/20 |
| 0.84 | 3/25 | 2/20 |
| 0.86 | 3/25 | 1/20 |
| 0.88 | 3/25 | 1/20 |
| 0.90 | 3/25 | 1/20 |
| 0.92 | 3/25 | 0/20 |
| 0.94 **←** | 1/25 | 0/20 |
| 0.96 | 0/25 | 0/20 |
| 0.98 | 0/25 | 0/20 |

## Uncacheable questions the cache would still look up: 0


## Paraphrases

| Pair | Similarity | Cacheable | Same signature |
| --- | --- | --- | --- |
| same-01 قیمت هاتون چطوریه؟ / قیمتتون چیه؟ | 0.950 | yes | yes |
| same-02 قیمتا چنده؟ / هزینه سانس ها چقدره؟ | 0.419 | yes | yes |
| same-03 نرخ سانس ها چنده / قیمت هر سانس چقدره | 0.645 | yes | yes |
| same-04 ساعت کاریتون چیه؟ / تا کی بازید؟ | 0.289 | yes | yes |
| same-05 چطوری آنلاین نوبت بگیرم؟ / چجوری میشه اینترنتی رزرو کرد؟ | 0.591 | yes | yes |
| same-06 میتونم رزروم رو کنسل کنم؟ / لغو رزرو امکانش هست؟ | 0.424 | yes | yes |
| same-07 باشگاه مشتریان فعاله؟ / میشه عضو باشگاه شد؟ | 0.640 | yes | yes |
| same-08 پرداخت با چه درگاهیه؟ / با چه بانکی پول بدم؟ | 0.692 | yes | yes |
| same-09 بعد از انتخاب سانس چقدر وقت دارم پول بدم؟ / چند دقیقه فرصت دارم برای پرداخت؟ | 0.422 | yes | yes |
| same-10 بعد از پرداخت کد رزرو کجا میاد؟ / کد رزرو رو از کجا بگیرم؟ | 0.664 | yes | yes |
| same-11 تو هر سانس چند نفر میتونن سوار بشن؟ / ظرفیت هر سانس چنده؟ | 0.781 | yes | yes |
| same-12 چند تا ماشین دارید؟ / تعداد خودروها چنده؟ | 0.763 | yes | yes |
| same-13 شماره تلفن برای رزرو چنده؟ / با چه شماره ای میتونم برای رزرو تماس بگیرم؟ | 0.938 | yes | yes |
| same-14 برای فردا میشه رزرو کرد؟ / فردا نوبت دارید؟ | 0.777 | yes | yes |
| same-15 How much does it cost? / What are your prices? | 0.598 | NO | yes |
| same-16 What time do you open? / What are your opening hours? | 0.779 | yes | yes |
| same-17 How can I book? / How do I make a reservation? | 0.227 | yes | yes |
| same-18 آدرس پیست کجاست؟ / کجا هستید؟ | 0.595 | yes | yes |
| same-19 باشگاه مشتریان چیه؟ / باشگاه داوس چه امکاناتی داره؟ | 0.718 | yes | yes |
| same-20 از چه درگاهی پرداخت میشه؟ / درگاه پرداختتون کدومه؟ | 0.827 | yes | yes |
| same-21 آیا رزرو تلفنی هم دارید؟ / میشه تلفنی نوبت گرفت؟ | 0.468 | yes | yes |
| same-22 لغو رزرو چطوریه؟ / چطوری رزروم رو لغو کنم؟ | 0.487 | yes | yes |
| same-23 سلام، ببخشید قیمت هر خودرو چقدر میشه؟ / هزینه هر ماشین چقدره؟ | 0.921 | yes | yes |
| same-24 آیا امکان رزرو آنلاین وجود دارد؟ / از سایت هم میشه رزرو کرد؟ | 0.741 | yes | NO |
| same-25 چقدر باید پول بدم؟ / قیمت چقدره؟ | 0.556 | yes | yes |

## Look-alikes (must never be served for each other)

| Pair | Similarity | Stopped by |
| --- | --- | --- |
| diff-01 قیمت تک نفره روز عادی چنده؟ / قیمت تک نفره روز تعطیل چنده؟ | 0.716 | the signature (a deciding word differs) |
| diff-02 قیمت تک نفره چنده؟ / قیمت دونفره چنده؟ | 0.690 | the signature (a deciding word differs) |
| diff-03 رزرو آنلاین چطوریه؟ / رزرو تلفنی چطوریه؟ | 0.696 | the signature (a deciding word differs) |
| diff-04 آیا آنلاین میشه پرداخت کرد؟ / آیا تلفنی میشه پرداخت کرد؟ | 0.661 | the signature (a deciding word differs) |
| diff-05 بچه ها هم میتونن سوار بشن؟ / بزرگسالها هم میتونن سوار بشن؟ | 0.690 | the signature (a deciding word differs) |
| diff-06 میشه رزرو کرد؟ / نمیشه رزرو کرد؟ | 0.593 | the signature (a deciding word differs) |
| diff-07 هزینه لغو رزرو چقدره؟ / هزینه رزرو چقدره؟ | 0.830 | the similarity threshold only |
| diff-08 مدت نگه داشتن سانس برای پرداخت چقدره؟ / مدت هر سانس چقدره؟ | 0.856 | the similarity threshold only |
| diff-09 در هر سانس چند نفر جا دارد؟ / در هر روز چند سانس داریم؟ | 0.798 | the similarity threshold only |
| diff-10 باشگاه مشتریان فعاله؟ / باشگاه مشتریان چیه؟ | 0.912 | the similarity threshold only |
| diff-11 قیمت سانس چنده؟ / مدت سانس چنده؟ | 0.522 | the similarity threshold only |
| diff-12 شماره تلفن رزرو چنده؟ / شماره رزرو من چیه؟ | 0.760 | the similarity threshold only |
| diff-13 کد رزرو کجا میاد؟ / کد تایید ورود کجا میاد؟ | 0.768 | the similarity threshold only |
| diff-14 پرداخت چطوریه؟ / برگشت پول چطوریه؟ | 0.555 | the similarity threshold only |
| diff-15 اگر پرداخت موفق باشه چی میشه؟ / اگر پرداخت ناموفق باشه چی میشه؟ | 0.715 | the similarity threshold only |
| diff-16 رزرو آنلاین باز است؟ / رزرو آنلاین بسته است؟ | 0.516 | the similarity threshold only |
| diff-17 Can I book online? / Can I book by phone? | 0.687 | the signature (a deciding word differs) |
| diff-18 قیمت خودرو چقدره؟ / قیمت لباس مناسب چقدره؟ | 0.468 | the signature (a deciding word differs) |
| diff-19 ساعت شروع اولین سانس چنده؟ / ساعت پایان آخرین سانس چنده؟ | 0.748 | the similarity threshold only |
| diff-20 برای فردا میشه رزرو کرد؟ / برای امروز میشه رزرو کرد؟ | 0.862 | the eligibility rule (age, day, hour, ... in one question) |
