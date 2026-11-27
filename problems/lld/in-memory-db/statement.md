# In-memory Database (mini SQL)

Design a tiny relational store: tables with a primary key, CRUD with simple filters, and
secondary indexes. All values are strings.

## Requirements

1. `create_table(name, columns, primary_key)`: empty or repeated columns, or a primary key
   not among the columns → `InvalidSchema`; repeated name → `DuplicateTable`.
2. `insert(table, row)`: the row must have exactly the table's columns → `InvalidRow`;
   an existing primary key → `DuplicateKey`.
3. `select(table, where, order_by, limit)`: `where` is a map of `column → value`
   (all must match; empty = all rows). Results are ordered by `order_by` ascending (string
   order), ties by primary key; `order_by = ""` means by primary key. `limit = 0` means no
   limit (`limit < 0` → `InvalidQuery`).
4. `update(table, where, values)` sets columns on all matching rows and returns the count.
   If the update would give two rows the same primary key (or clash with an existing one)
   → `DuplicateKey` and **nothing** changes.
5. `delete(table, where)` returns how many rows were removed.
6. `create_index(table, column)`: subsequent equality filters on that column should not
   scan the table. Results are identical with or without the index.
7. Unknown table → `UnknownTable`; unknown column anywhere → `UnknownColumn`.
8. Writers and readers run concurrently: primary keys stay unique.

## Things an interviewer will push on

- How do indexes stay consistent on update and delete?
- How would you add range queries (`>`, `<`) or joins?
- What would transactions look like on top of this?
