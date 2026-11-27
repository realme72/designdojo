create table users (id int primary key, signed_up_at timestamptz not null);
create table activity (user_id int not null references users (id), active_on date not null);
