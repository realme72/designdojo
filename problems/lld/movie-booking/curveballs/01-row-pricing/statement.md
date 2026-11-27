# Row pricing

Back rows cost more. `set_row_price(show_id, row, price)` prices every seat in a row (rows
never priced cost 0). Bookings gain a `total`: the sum of their seats' prices **at the moment
the hold was placed**, so a later price change doesn't affect an existing hold. A row letter
outside the layout raises `InvalidSeat`.

*Interviewer's question:* where does the price live: the seat, the row, the show, or a policy?
