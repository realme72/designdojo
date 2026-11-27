create table sensors (id int primary key, name text not null);
create table readings (sensor_id int not null references sensors (id), ts timestamptz not null, value numeric(8, 2) not null);
