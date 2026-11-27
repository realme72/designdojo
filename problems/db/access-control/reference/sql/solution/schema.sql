create table users (id bigint generated always as identity primary key, name text not null);
create table roles (id bigint generated always as identity primary key, name text not null unique);
create table permissions (
  id       bigint generated always as identity primary key,
  resource text not null,
  action   text not null,
  unique (resource, action)
);
create table role_permissions (
  role_id       bigint not null references roles (id),
  permission_id bigint not null references permissions (id),
  primary key (role_id, permission_id)
);
create index role_permissions_perm_idx on role_permissions (permission_id);
create table user_roles (
  user_id bigint not null references users (id),
  role_id bigint not null references roles (id),
  primary key (user_id, role_id)
);
create index user_roles_role_idx on user_roles (role_id);
create table role_parents (
  role_id   bigint not null references roles (id),
  parent_id bigint not null references roles (id),
  primary key (role_id, parent_id),
  check (role_id <> parent_id)
);
create index role_parents_parent_idx on role_parents (parent_id);

create function no_role_cycle() returns trigger language plpgsql as $$
begin
  if exists (
    with recursive up (id) as (
      select new.parent_id
      union
      select p.parent_id from role_parents p join up on p.role_id = up.id
    )
    select 1 from up where id = new.role_id
  ) then
    raise exception 'role inheritance cycle';
  end if;
  return new;
end $$;
create trigger role_parents_no_cycle before insert on role_parents for each row execute function no_role_cycle();

create view user_permissions as
with recursive effective (user_id, role_id) as (
  select user_id, role_id from user_roles
  union
  select e.user_id, p.parent_id from effective e join role_parents p on p.role_id = e.role_id
)
select distinct e.user_id, pm.resource, pm.action
from effective e join role_permissions rp on rp.role_id = e.role_id join permissions pm on pm.id = rp.permission_id;
