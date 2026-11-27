# Issue Tracker (Jira)

> **Interview questions** (tab next to Problem): start there.

Design the core of an issue tracker (**PostgreSQL 17**).

## Requirements

1. **Projects** have a unique key (2–10 capital letters, e.g. `DOJO`) and **members** (users).
2. **Issues** are numbered **per project**, 1, 2, 3 … with no gaps or duplicates, shown as
   `DOJO-1`. An issue has a title, a reporter and an optional assignee; both must be members of
   that project.
3. Status workflow: `TODO → IN_PROGRESS → DONE`, and `IN_PROGRESS → TODO`. Every status change
   is recorded in an **audit history** with its time.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `create_project(:key, :name)` | one row: `id` |
| `add_member(:project_id, :user_id)` | nothing |
| `create_issue(:project_id, :title, :reporter_id)` | one row: `issue_key` |
| `assign(:issue_key, :user_id)` | nothing |
| `move(:issue_key, :status, :at)` | nothing |
| `board(:project_id)` | rows `status`, `issue_key`, `assignee`: TODO, IN_PROGRESS, DONE order, then issue number; assignee NULL if none |
| `history(:issue_key)` | rows `from_status`, `to_status`: in order |
| `workload(:project_id)` | rows `name`, `open`: every member with their assigned issues that aren't DONE, by open desc then name |
