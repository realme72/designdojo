# Immediate-or-cancel

Traders want a new order type, `IOC`: it has a limit price like `LIMIT`, trades whatever
crosses immediately, and cancels the rest instead of resting on the book (status `CANCELLED`
if anything is left over, `FILLED` otherwise). Price must be at least 1, like a limit order.

*Interviewer's question:* how many places switch on order type?
