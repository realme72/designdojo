# Insurance add-on

Customers can add insurance to a reservation: `add_insurance(rental_id, per_day)` (only while
`RESERVED`, else `InvalidState`; unknown id → `UnknownRental`). The bill gets a new line,
`insurance = per_day × booked days`, included in `total`. Rentals without insurance show 0.

*Interviewer's question:* how many places changed to add one fee line?
