insert into employees (name, department_id, manager_id, salary, hired_on) values (:name, :department_id, :manager_id, :salary, :hired_on) returning id;
