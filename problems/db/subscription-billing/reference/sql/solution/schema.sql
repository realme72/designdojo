create extension if not exists btree_gist;

create table plans (
  id            bigint generated always as identity primary key,
  code          text not null unique,
  monthly_price numeric(10, 2) not null check (monthly_price >= 0)
);
create table customers (id bigint generated always as identity primary key, email text not null unique);

create table subscriptions (
  id          bigint generated always as identity primary key,
  customer_id bigint not null references customers (id),
  plan_id     bigint not null references plans (id),
  start_at    timestamptz not null,
  end_at      timestamptz,
  check (end_at is null or end_at > start_at),
  exclude using gist (customer_id with =, tstzrange(start_at, end_at) with &&)   -- one active at a time
);
create index subscriptions_plan_idx on subscriptions (plan_id);

create table invoices (
  id              bigint generated always as identity primary key,
  subscription_id bigint not null references subscriptions (id),
  period_start    date not null,
  amount          numeric(10, 2) not null check (amount >= 0),
  unique (subscription_id, period_start)   -- each period billed once
);
