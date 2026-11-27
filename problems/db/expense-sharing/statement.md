# Expense Sharing (Splitwise)

> **Interview questions** (tab next to Problem): start there.

Design the database for splitting group expenses (**PostgreSQL 17**).

## Requirements

1. **Users** have a name. **Groups** have a name and **members**.
2. An **expense** in a group has a payer, an amount (> 0, 2 decimals) and a description; it is
   split into **shares** among group members. Payer and everyone sharing must be **members of
   that group**. Shares always add up to exactly the amount.
3. **Equal splits** divide to the cent; leftover cents go one each to the first participants
   in the order given (100.00 / 3 = 33.34, 33.33, 33.33).
4. Members **settle up** by paying each other (a payment from one member to another).

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `create_group(:name)` | one row: `id` |
| `add_member(:group_id, :user_id)` | nothing |
| `add_expense_equal(:group_id, :paid_by, :amount, :description, :participants)` | one row: `id` (`:participants`: user ids, in order) |
| `add_expense_exact(:group_id, :paid_by, :amount, :description, :shares)` | one row: `id` (`:shares` JSON `[{"user_id": 1, "amount": 12.50}, ...]`; rejected unless they sum to the amount) |
| `settle(:group_id, :from_id, :to_id, :amount)` | nothing |
| `balances(:group_id)` | rows `name`, `balance`: per member, paid + settlements sent − shares − settlements received… i.e. **positive = is owed money**; by name |
| `expense_shares(:expense_id)` | rows `name`, `share`, by name |
