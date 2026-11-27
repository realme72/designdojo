# URL Shortener

Design the core of a URL shortener (think bit.ly) running in one process.

## Requirements

1. `shorten(long_url, alias, ttl_seconds)` returns a short code.
   - `long_url` must start with `http://` or `https://` → else `InvalidUrl`.
   - `alias = ""` → auto code: the next sequence number `n = 1, 2, 3, …` encoded in
     base62 (alphabet `0-9a-zA-Z`), left-padded with `0` to 6 characters (`n=1 → "000001"`,
     `n=62 → "000010"`). If that code is already taken, skip to the next `n`.
   - A custom alias must match `[A-Za-z0-9_-]{3,30}` → else `InvalidAlias`; taken →
     `AliasTaken`.
   - Auto codes are deduplicated: shortening a URL that already has an **active auto code**
     returns that code (aliases never dedupe).
   - `ttl_seconds = 0` means never expires; otherwise the code expires when
     `now ≥ created + ttl_seconds`.
2. `resolve(code)` returns the long URL and counts a click. Unknown or deleted →
   `UnknownCode`; expired → `Expired`.
3. `clicks(code)` returns the click count (`UnknownCode` if never existed or deleted).
   `delete(code)` removes a code (`UnknownCode` if absent).
4. Shortening and resolving happen concurrently: codes are unique and no click is lost.

## Things an interviewer will push on

- Counter + base62 vs hashing: collisions, predictability, distribution across servers?
- How do you scale the read path (caching, redirects)?
- Where does expiry live: on read, or a cleanup job?
