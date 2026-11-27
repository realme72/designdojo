create table pageviews (id int primary key, user_id int not null, url text not null, viewed_at timestamptz not null);
