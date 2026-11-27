create table accounts (id int primary key, owner text not null);
create table transactions (
  id         int primary key,
  account_id int not null references accounts (id),
  posted_at  timestamptz not null,
  amount     numeric(12, 2) not null   -- positive = credit, negative = debit
);
