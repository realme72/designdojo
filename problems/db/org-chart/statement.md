# Org Chart & Salaries

> **Interview questions** (tab next to Problem): start there.

Design the employee hierarchy of a company and answer the classic questions about it
(**PostgreSQL 17**).

## Requirements

1. **Departments** have a unique name. **Employees** have a name, a department, a salary (> 0),
   a hire date and a manager (another employee; NULL only for the CEO).
2. Nobody manages themselves, and the reporting lines never form a cycle.

## Operations

| Operation | Returns |
|---|---|
| `add_department(:name)` | one row: `id` |
| `hire(:name, :department_id, :manager_id, :salary, :hired_on)` | one row: `id` |
| `set_manager(:employee_id, :manager_id)` | nothing |
| `chain(:employee_id)` | rows `name`, `level`: the employee (level 0), their manager (1), … up to the top |
| `team_size(:employee_id)` | a single value: everyone below the employee, directly or indirectly |
| `top_paid(:n)` | rows `department`, `name`, `salary`: per department, everyone whose salary is among its `n` highest **distinct** salaries; by department, salary desc, name |
| `dept_stats()` | rows `department`, `headcount`, `avg_salary` (2 decimals, NULL if empty), `max_salary`: every department, by name |
| `earns_more_than_manager()` | rows `name`, `manager`: by name |
