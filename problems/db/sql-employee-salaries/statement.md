# Employee Salaries

> **Interview questions** (tab next to Problem): start there.

The schema is given (`contract/schema.sql`): `departments(id, name)` and
`employees(id, name, department_id, manager_id, salary)`. Write the queries. Each test loads
different data.

| Query | Returns |
|---|---|
| `nth_highest(:n)` | a single value: the n-th highest **distinct** salary, NULL if there isn't one |
| `top3_per_department()` | rows `department`, `name`, `salary`: employees whose salary is among the department's 3 highest distinct salaries; by department, salary desc, name |
| `above_department_average()` | rows `name`, `department`: paid strictly more than their department's average; by name |
| `managers_with_reports(:min)` | rows `name`, `reports`: managers with at least `:min` direct reports; by reports desc, name |
