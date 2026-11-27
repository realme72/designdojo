select employee, quartile from (
  select employee, salary, id, ntile(4) over (order by salary, id) as quartile from salaries
) x order by quartile, salary, id;
