# Restaurant Table Reservations

> **Interview questions** (tab next to Problem): start there.

Design table reservations for a restaurant (**PostgreSQL 17**).

## Requirements

1. **Tables** have a unique label and a number of seats (2–12).
2. A **reservation** is for a guest name and a party size (≥ 1) at a start time, and lasts
   exactly **2 hours**. It is assigned to one table.
3. A table can't have two overlapping reservations (back-to-back is fine). Cancelled
   reservations free the table.
4. Reserving assigns the **smallest table that fits** the party and is free for the whole
   2 hours (ties: lowest label). If none fits, the request is rejected.

## Operations

| Operation | Returns |
|---|---|
| `add_table(:label, :seats)` | one row: `id` |
| `reserve(:guest, :party_size, :starts_at)` | one row: `reservation_id`, `table_label` |
| `cancel(:reservation_id)` | nothing |
| `free_tables(:at)` | rows `label`, `seats`: tables with no reservation covering `:at`, by seats then label |
| `covers(:day)` | a single value: total guests of reservations starting that UTC day (0 if none) |
