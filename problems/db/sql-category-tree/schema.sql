create table categories (id int primary key, parent_id int references categories (id), name text not null);
create table products (id int primary key, category_id int not null references categories (id), name text not null, price numeric(10, 2) not null);
