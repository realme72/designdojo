with m as (select company, percentile_cont(0.5) within group (order by salary) as median from salaries group by company)
select s.company, s.employee from salaries s join m on m.company = s.company
where s.salary > m.median order by s.company, s.employee;
