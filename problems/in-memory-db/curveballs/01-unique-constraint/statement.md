# Unique constraints

Emails must be unique. `add_unique(table, column)` adds a constraint: afterwards any insert or
update that would leave two rows with the same value in that column raises `DuplicateKey`
and changes nothing. Adding it to a column that already has duplicates raises `InvalidSchema`.
Unknown table/column → `UnknownTable` / `UnknownColumn`.

*Interviewer's question:* the primary key was already a unique constraint. Is it still special?
