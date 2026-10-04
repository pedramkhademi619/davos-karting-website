# Assistant evaluation: held_out_final

2026-10-04 18:42 UTC · model `gemma-3-27b-it` · commit `051fd91+dirty` · rules `96bf316fc6d7e1b9` · persona `770ff29135c7` · knowledge `5f1bfb6b6ebd`

| Metric | Value |
| --- | --- |
| Questions × repeats | 24 × 3 = 72 |
| Pass rate (95 % CI) | **95.8%** (88.5% - 98.6%) |
| Pass rate without provider failures | 95.8% |
| Right in every repeat (pass^k) | 95.8% |
| Answered by the model | 100.0% of questions |
| Needed a repair call | 23.6% of model-answered questions |
| Provider failures | 0 |
| Prompt tokens per model-answered question | 3598 |
| Served from the provider cache | 72.6% of prompt tokens |
| Completion tokens per model-answered question | 14 |
| Cost per 1000 questions (provider-reported) | $0.213 |
| Spent on this evaluation (answers + judge) | $0.0153 |
| Latency p50 / p95 (model-answered) | 1.1 s / 3.6 s |

## By category

| Category | Passed | Rate |
| --- | --- | --- |
| held_out_unknown | 69/72 | 96% |

## Outcomes

- `answered`: 6
- `insufficient_information`: 66

## Failures (3)

- **heldout-23** (repeat 1, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه ای نداریم. فعلا فقط باشگاه مشتریان داریم که هنوز راه نیفتاده.
- **heldout-23** (repeat 2, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه ای نداریم. فعلاً فقط باشگاه مشتریان داریم که هنوز راه‌اندازی نشده.
- **heldout-23** (repeat 3, answered without deferring to the venue): برای دانش‌آموزا تخفیف مدرسه ای دارید؟
  - reply: متاسفانه نه، تخفیف مدرسه‌ای نداریم. فعلاً فقط باشگاه مشتریان داریم که هنوز راه‌اندازی نشده.
