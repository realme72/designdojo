# Roles & Permissions (RBAC)

> **Interview questions** (tab next to Problem): start there.

Design role-based access control with role inheritance (**PostgreSQL 17**).

## Requirements

1. **Users**; **roles** (unique name); **permissions** = (resource, action), unique together.
2. Roles are **granted** permissions; users are **assigned** roles (each pair at most once).
3. A role can **inherit** other roles (an `admin` inherits `editor` which inherits `viewer`) and
   gets all their permissions, transitively. Inheritance can't form a cycle (or inherit
   itself).

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)`, `add_role(:name)` | one row: `id` |
| `add_permission(:resource, :action)` | one row: `id` |
| `grant(:role_id, :permission_id)`, `assign(:user_id, :role_id)` | nothing |
| `inherit(:role_id, :parent_id)` | nothing (`:role_id` gets everything `:parent_id` has) |
| `can(:user_id, :resource, :action)` | a single value: true/false |
| `permissions_of(:user_id)` | rows `resource`, `action`: effective permissions, by resource then action |
| `who_can(:resource, :action)` | rows `name`: users with that effective permission, by name |
