# Load & concurrency tests

Plain-stdlib Python harnesses (no external deps) used to characterise the booking system under load.
Run them against a running stack (see the repo's compose files).

- **`rush_single_session.py`** — the "everyone grabs the last slot" test. Creates many customers, logs them in,
  then fires simultaneous holds at one session. Proves no double-booking: only capacity-many `201`s, the rest `409`.
  Run inside a container on the backend network to bypass the edge rate-limit:
  `docker run --rm --network davos_backend -v $PWD/load-tests/rush_single_session.py:/r.py:ro -e BASE=http://api:8000 davos-api:dev python /r.py`

- **`read_endpoint_throughput.py`** — sustained throughput/latency of the public read endpoints.
  `docker run --rm --network davos_backend -v $PWD/load-tests/read_endpoint_throughput.py:/l.py:ro -e BASE=http://api:8000 -e VU=24 -e DUR=20 davos-api:dev python /l.py`

The chatbot/assistant is intentionally excluded (it calls an external model).
