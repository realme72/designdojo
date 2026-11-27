# Median & Percentiles

> **Interview questions** (tab next to Problem): start there.

Schema given: `salaries(id, company, employee, salary)`.

| Query | Returns |
|---|---|
| `median_by_company()` | rows `company`, `median`: continuous median (average of the two middle values for even counts), by company |
| `percentile(:p)` | a single value: the continuous `:p` percentile (0–1) of all salaries, rounded to 2 decimals |
| `above_median()` | rows `company`, `employee`: employees paid strictly above their company's median, by company then employee |
| `salary_quartiles()` | rows `employee`, `quartile`: quartile 1–4 by salary ascending (ties: id) across everyone, by quartile, salary, id |
