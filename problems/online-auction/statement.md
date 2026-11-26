# Online Auction (eBay)

Design timed auctions with bidding rules and anti-sniping.

## Requirements

1. `create_auction(auction_id, seller, starting_price, min_increment, ends_at)`:
   `starting_price < 1`, `min_increment < 1` or `ends_at ≤ now` → `InvalidAuction`;
   repeated id → `DuplicateAuction`.
2. `bid(auction_id, bidder, amount)`. Checks, in order: `UnknownAuction`; the auction is
   over (`now ≥ ends_at`, or closed) → `AuctionClosed`; the seller bidding → `SelfBid`;
   the first bid must be ≥ `starting_price`, later bids ≥ current highest + `min_increment`
   → `BidTooLow`. Returns `{highest, ends_at}` after the bid.
3. **Anti-sniping**: a bid accepted when fewer than `extension_window` seconds remain
   (`ends_at − now < extension_window`, config) pushes `ends_at` to `now + extension`.
4. `highest(auction_id)` → `{bidder, amount}` (no bids → `NoBids`).
   `history(auction_id)` → accepted bids in order.
5. `close(auction_id)` after the end → `{winner, price}` (empty winner and 0 if there were
   no bids). Before the end → `AuctionOpen`. Closing again returns the same result.
6. Bids race at the last second: the accepted bids must form a strictly increasing
   sequence, and the true highest bid must win.

## Things an interviewer will push on

- How would you add proxy (automatic) bidding or reserve prices?
- Where do bid-validation rules live?
- How do you close auctions on time without a timer per auction?
