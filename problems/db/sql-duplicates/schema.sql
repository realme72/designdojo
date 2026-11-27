create table signups (
  id         int primary key,
  email      text not null,
  name       text not null,
  created_at timestamptz not null
);
