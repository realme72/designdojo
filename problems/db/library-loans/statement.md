# Library Loans

> **Interview questions** (tab next to Problem): start there.

Design a lending library's database (**PostgreSQL 17**).

## Requirements

1. A **book** (title, unique ISBN) has physical **copies**, each with a unique barcode.
2. **Members** borrow copies. A copy can be on **one active loan** at a time; a member can have
   at most **3 active loans**.
3. A loan is due **14 days** after checkout. Returning late costs **10.00 per started day**
   late.

## Operations

| Operation | Returns |
|---|---|
| `add_book(:isbn, :title)` | one row: `id` |
| `add_copy(:book_id, :barcode)` | one row: `id` |
| `add_member(:name)` | one row: `id` |
| `checkout(:barcode, :member_id, :at)` | one row: `loan_id`, `due_at` |
| `return_copy(:barcode, :at)` | one row: `fine` (rejected if the copy isn't on loan) |
| `available_copies(:isbn)` | a single value |
| `overdue(:at)` | rows `member`, `title`, `days_overdue` (started days): active loans past due at `:at`, most overdue first, then member |
