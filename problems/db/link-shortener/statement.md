# Link Shortener Analytics (Bitly)

> **Interview questions** (tab next to Problem): start there.

Design storage and analytics for short links (**PostgreSQL 17**).

## Requirements

1. A **link** has a unique short code (case-sensitive), a target URL (must start with
   `http://` or `https://`), an owner, a creation time and an optional expiry time.
2. **Resolving** a code returns the target URL and records a **click** (time, country) — only
   if the link exists and hasn't expired. Expired or unknown codes resolve to nothing and record
   no click.

## Operations

| Operation | Returns |
|---|---|
| `create_link(:code, :url, :owner, :created_at, :expires_at)` | one row: `id` |
| `resolve(:code, :at, :country)` | one row: `url` |
| `top_links(:owner, :n)` | rows `code`, `clicks`: the owner's links by clicks desc, then code (links with 0 clicks included) |
| `daily_clicks(:code, :from_day, :to_day)` | rows `day`, `clicks`: every UTC day in `[from_day, to_day]`, zero days included |
| `countries(:code)` | rows `country`, `clicks`, `share`: per country, share as a percentage with 1 decimal; by clicks desc then country |
