# Multi-Tenant SaaS

> **Interview questions** (tab next to Problem): start there.

Design a task-management SaaS where many companies (**tenants**) share one database
(**PostgreSQL 17**). Data must never leak between tenants.

## Requirements

1. **Tenants** have a unique slug and a plan: `FREE` or `PRO`.
2. **Users** belong to one tenant; emails are unique **within a tenant** (the same email may
   exist in two tenants).
3. **Projects** belong to a tenant (names unique within it). A `FREE` tenant can have at most
   **3 projects**.
4. **Tasks** belong to a project and may be assigned to a user, who must be in the **same
   tenant** as the project. Cross-tenant references of any kind must be impossible.

## Operations

| Operation | Returns |
|---|---|
| `add_tenant(:slug, :plan)` | one row: `id` |
| `add_user(:tenant_id, :email)` | one row: `id` |
| `create_project(:tenant_id, :name)` | one row: `id` |
| `create_task(:tenant_id, :project_id, :title, :assignee_id)` | one row: `id` (`:assignee_id` may be NULL) |
| `upgrade(:tenant_id)` | nothing: becomes PRO |
| `user_tasks(:tenant_id, :user_id)` | rows `project`, `title`: by project then title |
| `usage()` | rows `slug`, `plan`, `users`, `projects`, `tasks`: every tenant, by slug |
