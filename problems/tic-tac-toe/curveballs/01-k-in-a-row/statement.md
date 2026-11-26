# K in a row

Bigger boards need shorter winning lines. `set_win_length(k)` (before the first move of a
game; `3 <= k <= size`) makes any `k` consecutive marks in a row, column or diagonal (either
direction, anywhere on the board) win. The default stays `size`. The setting survives
`reset`. Invalid `k`, or calling it after a move, raises `InvalidMove`.

*Interviewer's question:* does your O(1) win check survive this, and does it need to?
