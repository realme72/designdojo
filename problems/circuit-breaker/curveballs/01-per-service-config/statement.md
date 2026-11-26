# Per-service settings

The payments service is flakier than the rest. Add `configure(service, failure_threshold,
open_seconds, trial_requests)`: that service's breaker uses these settings from now on
(others keep the defaults) and restarts `CLOSED`. Services configured before their first call
use the override from the start.

*Interviewer's question:* who owns the configuration: the registry, the breaker, or its states?
