create table salaries (
  id       int primary key,
  company  text not null,
  employee text not null,
  salary   int not null check (salary > 0)
);
