# Professional Network (LinkedIn)

> **Interview questions** (tab next to Problem): start there.

Connections are **mutual**: one user sends a request, the other accepts (**PostgreSQL 17**).

## Requirements

1. **Users** have a name.
2. A user can send a connection **request** to another user: not to themselves, not to someone
   they're already connected with, and not while a request between the two is pending **in
   either direction**.
3. **Accepting** turns a pending request into a connection. Accepting a request that doesn't
   exist (or isn't pending) is rejected.
4. A connection is one fact about a pair: A–B and B–A are the same connection.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `request(:from_id, :to_id)` | nothing |
| `accept(:from_id, :to_id)` | nothing (`:to_id` accepts `:from_id`'s request) |
| `connections(:user_id)` | rows `name`, by name |
| `mutual(:a_id, :b_id)` | rows `name`: people connected to both, by name |
| `degree(:from_id, :to_id)` | a single value: 1 for a direct connection, 2 for a connection of a connection, 3 …; NULL if not within 3 |
