create table people (id int primary key, name text not null);
-- each friendship stored ONCE, with user_a < user_b
create table friendships (
  user_a int not null references people (id),
  user_b int not null references people (id),
  primary key (user_a, user_b),
  check (user_a < user_b)
);
