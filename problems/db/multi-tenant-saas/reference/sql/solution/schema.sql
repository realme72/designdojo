create table tenants (
  id   bigint generated always as identity primary key,
  slug text not null unique,
  plan text not null check (plan in ('FREE', 'PRO'))
);

create table users (
  id        bigint generated always as identity primary key,
  tenant_id bigint not null references tenants (id),
  email     text not null,
  unique (tenant_id, email),
  unique (tenant_id, id)
);

create table projects (
  id        bigint generated always as identity primary key,
  tenant_id bigint not null references tenants (id),
  name      text not null,
  unique (tenant_id, name),
  unique (tenant_id, id)
);

create table tasks (
  id          bigint generated always as identity primary key,
  tenant_id   bigint not null,
  project_id  bigint not null,
  title       text not null,
  assignee_id bigint,
  foreign key (tenant_id, project_id) references projects (tenant_id, id),
  foreign key (tenant_id, assignee_id) references users (tenant_id, id)   -- same tenant only
);
create index tasks_project_idx on tasks (tenant_id, project_id);
create index tasks_assignee_idx on tasks (tenant_id, assignee_id);

create function free_plan_limit() returns trigger language plpgsql as $$
declare p text;
begin
  select plan into p from tenants where id = new.tenant_id for update;   -- serialize per tenant
  if p = 'FREE' and (select count(*) from projects where tenant_id = new.tenant_id) >= 3 then
    raise exception 'FREE plan allows 3 projects';
  end if;
  return new;
end $$;
create trigger projects_plan_limit before insert on projects for each row execute function free_plan_limit();
