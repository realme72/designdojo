# Holds

When every copy is out, members can queue: `place_hold(member_id, isbn)` returns their position
in the queue (1 = next). When a copy comes back and someone is waiting, it is set aside for the
first member in the queue: it no longer counts as `available`, and only that member can check
it out (others get `NotAvailable`). Placing a hold while a copy is available, or holding the same
book twice, raises `InvalidState`.

*Interviewer's question:* who reacts when a book is returned?
