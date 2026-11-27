# Duplicate Records Cleanup

> **Interview questions** (tab next to Problem): start there.

Schema given: `signups(id, email, name, created_at)`. The same person signed up several times;
emails differ only in **case and surrounding spaces** (`' Ann@X.com'` = `'ann@x.com'`).

| Query | Returns |
|---|---|
| `duplicate_groups()` | rows `email`, `copies`: normalized emails (trimmed, lower-case) appearing more than once; by copies desc, email |
| `rows_to_delete()` | rows `id`: every row except the **earliest** signup of each normalized email (ties on time: lowest id); by id |
| `dedupe()` | rows `id`: **deletes** those rows and returns the deleted ids, by id |
| `remaining()` | a single value: rows left |
