select round(percentile_cont(:p::float8) within group (order by salary)::numeric, 2) from salaries;
