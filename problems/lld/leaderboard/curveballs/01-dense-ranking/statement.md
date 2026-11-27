# Dense ranking

Product wants an option for dense ranks (1, 1, 2 instead of 1, 1, 3). Add
`set_ranking_mode(mode)` with `COMPETITION` (the default and current behaviour) and `DENSE`
(rank = 1 + number of *distinct* higher scores). The mode applies to `rank`, `top` and
`around`, and can be switched back at any time.

*Interviewer's question:* where does "what is a rank" live in your design?
