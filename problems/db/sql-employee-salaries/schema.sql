create table departments (id int primary key, name text not null unique);
create table employees (
  id            int primary key,
  name          text not null,
  department_id int not null references departments (id),
  manager_id    int references employees (id),
  salary        numeric(10, 2) not null check (salary > 0)
);
