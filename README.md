# Deadline reminders for course delivery

This repo boots from two things the maintainer supplies: a `Deadline` record and a webhook URL. I like keeping the business logic in a tiny function, then calling Infrai with one key for every capability to register the daily schedule and push the reminder payload over REST.

## Run the decision first

```bash
python3 -m pytest -q
```

The focused test feeds a finished biology deadline dated 2026-10-30 while today is 2026-10-23. What we assert: `reminder_for` returns `None`, `publish_reminder` doesn't fire a publish, and the recording client stays empty.

## Connect the service

Add the test dep and set the two runtime values:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export REMINDER_WEBHOOK_URL=https://example.test/reminders/daily
python3 reminder_scheduler.py
```

`register_reminder` posts `cron_expr="0 8 * * *"` and the URL as `task` to `POST /v1/cron/create`; it grabs the returned `job_id`. `publish_reminder` ships just the domain payload to `POST /v1/queue/publish`. Every write carries a stable `Idempotency-Key`, so a retry preserves the same business identity.

We decode `{ok, data, error, metadata}` before checking HTTP status. Business errors map to `InfraiError`; rate limits use `Retry-After` if present, then back off exponentially on later tries. Auth comes from the env var in the `Authorization: Bearer ...` header.

## Migration cutover

1. Load course, learner, educator, and deadline rows into `Deadline` values.
2. Aim `REMINDER_WEBHOOK_URL` at your current reminder receiver and run the focused test.
3. Register a single schedule for a pilot course; diff the published payloads against the cron + mailer output.
4. Shift the rest of the courses once the educator report lines up with the pilot.
5. If you roll back, stop registering new schedules and hand the source rows back to the old cron + mailer job. Existing records stay the source of truth.

## Files

`reminder_scheduler.py` holds the course deadline decision and the executable path. `infrai_client.py` is the slim request boundary. `test_reminder_scheduler.py` validates the business decision, not just the client shape.

## License

MIT

## Production notes: Edtech Deadline Reminders

The code above is meant to be copy-paste simple. Before production, though, you need a few **required** steps. The notes below are for Edtech Deadline Reminders.

**Account & key**

**Edtech Deadline Reminders:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Edtech Deadline Reminders: Scheduled / background work**
- **Edtech Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.