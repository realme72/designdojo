# Seasonal rates

Holiday nights cost more. `set_seasonal_rate(type, start, end, percent)` makes every night in
`[start, end)` for rooms of that type cost `nightly_rate × percent / 100` (rounded down). If
seasons overlap, the one set last wins. It affects bookings made afterwards, not existing ones.
`end <= start` or a malformed date → `InvalidDates`.

*Interviewer's question:* your pricing policy knew the rate and the dates; what else does it need now?
