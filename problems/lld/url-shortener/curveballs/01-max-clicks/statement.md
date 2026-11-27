# Click limits

One-time download links. `set_max_clicks(code, n)`: after `n` successful resolves the link
behaves as expired (`Expired`), just like a TTL running out. `clicks` keeps counting successful
resolves only. Shortening the same URL again after its auto code is used up issues a fresh code.
Unknown code → `UnknownCode`; `n < 1` → `InvalidArgument`.

*Interviewer's question:* how many places decide whether a link is still alive?
