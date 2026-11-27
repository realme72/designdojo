create table users (id int primary key, name text not null);
create table logins (
  user_id   int not null references users (id),
  logged_at timestamptz not null
);
