create table users (id bigint generated always as identity primary key, name text not null);

create table projects (
  id          bigint generated always as identity primary key,
  key         text not null unique check (key ~ '^[A-Z]{2,10}$'),
  name        text not null,
  next_number int not null default 1
);

create table members (
  project_id bigint not null references projects (id),
  user_id    bigint not null references users (id),
  primary key (project_id, user_id)
);
create index members_user_idx on members (user_id);

create table issues (
  id          bigint generated always as identity primary key,
  project_id  bigint not null,
  number      int not null,
  title       text not null,
  reporter_id bigint not null,
  assignee_id bigint,
  status      text not null default 'TODO' check (status in ('TODO', 'IN_PROGRESS', 'DONE')),
  unique (project_id, number),
  foreign key (project_id, reporter_id) references members (project_id, user_id),
  foreign key (project_id, assignee_id) references members (project_id, user_id)
);
create index issues_assignee_idx on issues (project_id, assignee_id);

create table transitions (from_status text, to_status text, primary key (from_status, to_status));
insert into transitions values ('TODO', 'IN_PROGRESS'), ('IN_PROGRESS', 'DONE'), ('IN_PROGRESS', 'TODO');

create table issue_history (
  id          bigint generated always as identity primary key,
  issue_id    bigint not null references issues (id),
  from_status text not null,
  to_status   text not null,
  changed_at  timestamptz not null
);
create index issue_history_issue_idx on issue_history (issue_id, id);

create function check_issue_transition() returns trigger language plpgsql as $$
begin
  if new.status <> old.status and not exists
     (select 1 from transitions where from_status = old.status and to_status = new.status) then
    raise exception 'illegal transition % -> %', old.status, new.status;
  end if;
  return new;
end $$;
create trigger issues_transition before update of status on issues for each row execute function check_issue_transition();

create view issue_keys as select p.key || '-' || i.number as issue_key, i.* from issues i join projects p on p.id = i.project_id;
