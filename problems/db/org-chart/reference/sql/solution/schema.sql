create table departments (id bigint generated always as identity primary key, name text not null unique);

create table employees (
  id            bigint generated always as identity primary key,
  name          text not null,
  department_id bigint not null references departments (id),
  manager_id    bigint references employees (id),
  salary        numeric(12, 2) not null check (salary > 0),
  hired_on      date not null,
  check (manager_id <> id)
);
create index employees_manager_idx on employees (manager_id);
create index employees_department_idx on employees (department_id, salary desc);

create function no_management_cycle() returns trigger language plpgsql as $$
begin
  if new.manager_id is not null and exists (
    with recursive up (id) as (
      select new.manager_id
      union
      select e.manager_id from employees e join up on e.id = up.id where e.manager_id is not null
    )
    select 1 from up where id = new.id
  ) then
    raise exception 'management cycle';
  end if;
  return new;
end $$;
create trigger employees_no_cycle before update of manager_id on employees for each row execute function no_management_cycle();
