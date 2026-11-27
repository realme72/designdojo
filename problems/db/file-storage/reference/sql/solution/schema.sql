create table users (id bigint generated always as identity primary key, name text not null);

create table folders (
  id        bigint generated always as identity primary key,
  owner_id  bigint not null references users (id),
  parent_id bigint references folders (id),
  name      text not null check (name !~ '/' and length(name) > 0),
  check (parent_id <> id),
  unique nulls not distinct (owner_id, parent_id, name)   -- siblings, incl. the top level
);
create index folders_parent_idx on folders (parent_id);

create table files (
  id         bigint generated always as identity primary key,
  folder_id  bigint not null references folders (id),
  name       text not null check (name !~ '/' and length(name) > 0),
  size_bytes bigint not null check (size_bytes >= 0),
  unique (folder_id, name)
);

create table shares (
  folder_id bigint not null references folders (id),
  user_id   bigint not null references users (id),
  role      text not null check (role in ('VIEW', 'EDIT')),
  primary key (folder_id, user_id)
);
create index shares_user_idx on shares (user_id);

create function no_folder_cycle() returns trigger language plpgsql as $$
begin
  if new.parent_id is not null and exists (
    with recursive up (id) as (
      select new.parent_id
      union
      select f.parent_id from folders f join up on f.id = up.id where f.parent_id is not null
    )
    select 1 from up where id = new.id
  ) then
    raise exception 'cannot move a folder into itself';
  end if;
  return new;
end $$;
create trigger folders_no_cycle before update of parent_id on folders for each row execute function no_folder_cycle();
