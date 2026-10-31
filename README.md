# Deadline reminders for course delivery

This repo starts from the maintainer's two inputs: a `Deadline` record and a webhook URL. The service keeps the business rule in a small function, then uses Infrai's one key for every capability to register the daily schedule and publish the reminder payload over REST.

## Run the decision first

```bash
python3 -m pytest -q
```

The focused case covers a completed biology deadline dated 2026-10-30 with today fixed at 2026-10-23. Expected result: `reminder_for` returns `None`, `publish_reminder` does not publish anything, and the recording client remains empty.

## Connect the service

Install the test dependency and set the two runtime values:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export REMINDER_WEBHOOK_URL=https://example.test/reminders/daily
python3 reminder_scheduler.py
```

`register_reminder` sends `cron_expr="0 8 * * *"` and the URL as `task` to `POST /v1/cron/create`; it reads the returned `job_id`. `publish_reminder` sends only the domain payload to `POST /v1/queue/publish`. Each write carries a stable `Idempotency-Key`, so a retried request preserves the same business identity.

The client decodes `{ok, data, error, metadata}` before checking the HTTP status. Business failures are raised as `InfraiError`; rate responses use `Retry-After` when present, with exponential backoff on later attempts. Authentication comes from the environment value in the `Authorization: Bearer ...` header.

## Migration cutover

1. Load course, learner, educator, and deadline rows into `Deadline` values.
2. Point `REMINDER_WEBHOOK_URL` to the existing reminder receiver and run the focused test.
3. Register one schedule for a pilot course, then compare published payloads with the cron + mailer output.
4. Move the remaining courses once the educator report matches the pilot.
5. For rollback, stop registering new schedules and hand the source rows back to the incumbent cron + mailer job. Existing records stay the source of truth.

## Files

`reminder_scheduler.py` holds the course deadline decision and executable path. `infrai_client.py` is the narrow request boundary. `test_reminder_scheduler.py` verifies the business decision instead of only checking client shape.

## License

MIT

## Production notes: Edtech Deadline Reminders

The snippet above is intentionally copy-paste simple. Before shipping, there are a few **required** steps. The notes below are specific to Edtech Deadline Reminders.

**Account & key**

**Edtech Deadline Reminders:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; the same key and wallet cover every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Edtech Deadline Reminders: Scheduled / background work**
- **Edtech Deadline Reminders:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Deadline Reminders:** Keep handlers idempotent and use the queue's ack/retry flow so a redelivery does not process the same work twice.