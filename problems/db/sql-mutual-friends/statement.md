# Mutual Friends & Recommendations

> **Interview questions** (tab next to Problem): start there.

Schema given: `people(id, name)` and `friendships(user_a, user_b)` — each friendship is stored
**once** with `user_a < user_b`, but it goes both ways.

| Query | Returns |
|---|---|
| `friends(:person_id)` | rows `name`: by name |
| `mutual_friends(:a_id, :b_id)` | rows `name`: friends of both, by name |
| `recommendations(:person_id, :n)` | rows `name`, `mutuals`: people who aren't the person or their friends, with at least one mutual friend; by mutuals desc, name; top `n` |
| `most_connected(:n)` | rows `name`, `friends`: by friend count desc then name (people with 0 friends included), top `n` |
