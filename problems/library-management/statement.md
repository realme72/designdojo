# Library Management System

Design the lending core of a library: books with copies, members, loans, due dates and fines.

## Requirements

1. Config: `max_loans` per member, `loan_days`, `fine_per_day` (cents).
2. `add_book(isbn, title, author, copies)` adds a book, or adds copies to an existing ISBN
   (title/author stay as first added). `copies < 1` → `InvalidCopies`.
3. `add_member(member_id)`; repeated id → `DuplicateMember`.
4. `checkout(member_id, isbn)` lends one copy and returns the loan with
   `due_at = now + loan_days × 86400`. Checks, in order: `UnknownMember`, `UnknownBook`,
   member owes any fine → `OutstandingFines`, member at `max_loans` active loans →
   `LoanLimitReached`, no free copy → `NotAvailable`.
5. `return_book(loan_id)` ends the loan and returns the fine it incurred:
   `days_late × fine_per_day`, where days late = `ceil((now − due_at) / 86400)` when
   `now > due_at`, else 0. The fine is added to what the member owes. Unknown or already
   returned → `UnknownLoan`.
6. `pay_fine(member_id, amount)` returns what is still owed. `amount ≤ 0` or more than
   owed → `InvalidAmount`. `fines(member_id)` returns what is owed.
7. `available(isbn)` counts free copies. `loans(member_id)` lists active loans in checkout order.
8. `search(query)` returns ISBNs whose title or author contains `query` (case-insensitive),
   sorted by ISBN.
9. Many desks lend at once: never lend more copies than exist, never exceed `max_loans`.

## Things an interviewer will push on

- Book vs BookCopy vs Loan: which are entities and which are values?
- How would you add reservations (holds queue) or different member tiers?
- Where should fine policy live so it can change per member type?
