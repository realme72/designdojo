# Online Auctions

> **Interview questions** (tab next to Problem): start there.

Design the bidding database of an auction site (**PostgreSQL 17**). Two bids can arrive at the
same moment; the rules must still hold.

## Requirements

1. **Users** have a name. A seller **lists an item** with a title, a starting price (> 0) and an
   end time.
2. A **bid** has an amount and a time. It is accepted only if the auction hasn't ended, the
   bidder isn't the seller, and the amount is at least the starting price (first bid) or at
   least **1.00 more** than the current highest bid.
3. Bids are never edited or deleted.
4. When an auction has ended, its **winner** is the highest bidder.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `list_item(:seller_id, :title, :start_price, :ends_at)` | one row: `id` |
| `bid(:item_id, :bidder_id, :amount, :at)` | one row: `bid_id` |
| `bid_history(:item_id)` | rows `bidder`, `amount`: highest first |
| `results(:at)` | rows `title`, `winner`, `price`: auctions ended at `:at` that received bids, by title |
| `wins(:user_id, :at)` | a single value: auctions the user has won by `:at` |
