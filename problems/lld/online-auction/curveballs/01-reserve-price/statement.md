# Reserve price

Sellers can set a secret minimum: `set_reserve(auction_id, reserve)` (while the auction is
open; otherwise `AuctionClosed`). Bidding works as before, but on `close`, if the highest bid
is below the reserve, there is no sale: winner `""`, price 0. `reserve_met(auction_id)` tells
bidders only whether the current highest bid meets it (true when no reserve is set and there
is at least one bid).

*Interviewer's question:* which object decides the outcome of an auction?
