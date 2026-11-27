select company, percentile_cont(0.5) within group (order by salary) as median
from salaries group by company order by company;
