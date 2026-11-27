select (select distinct salary from employees order by salary desc offset :n - 1 limit 1) as salary;
