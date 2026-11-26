# Notification Service

Design a service that sends templated notifications over several channels.

## Requirements

1. Channels: `EMAIL`, `SMS`, `PUSH`. `set_preferences(user, channels)` sets which channels a
   user receives (none set → no channels).
2. `add_template(template_id, body)`: placeholders are `{name}` (letters, digits, `_`).
   Repeated id → `DuplicateTemplate`.
3. `send(user, template_id, vars, priority)` renders the template and delivers it on each of
   the user's channels **in channel order (EMAIL, SMS, PUSH)**, returning one
   `{channel, status, message}` per channel. Unknown template → `UnknownTemplate`; a
   placeholder without a value in `vars` → `MissingVariable` (nothing is sent). Extra vars are ignored.
4. Statuses:
   - `FAILED` if the channel's provider is down (`set_provider_down(channel, down)`).
   - `RATE_LIMITED` if the user already got `max_per_hour` (config) `SENT` messages on that
     channel in the last hour (`(now − 3600, now]`), unless `priority` is `HIGH`
     (high priority always goes through and still counts toward the limit).
   - Otherwise `SENT`.
5. `outbox(user, channel)` lists the messages `SENT` to that user on that channel, in order.
6. Sends happen concurrently: rate limits must hold exactly.

## Things an interviewer will push on

- How do you add a WhatsApp channel without touching send()?
- Where do rate limiting, retries and fallbacks sit (decorators / chain)?
- Sync vs async delivery: queues, retries, idempotency?
