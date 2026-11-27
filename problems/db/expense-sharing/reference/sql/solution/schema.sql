create table users (id bigint generated always as identity primary key, name text not null);
create table groups (id bigint generated always as identity primary key, name text not null);

create table members (
  group_id bigint not null references groups (id),
  user_id  bigint not null references users (id),
  primary key (group_id, user_id)
);
create index members_user_idx on members (user_id);

create table expenses (
  id          bigint generated always as identity primary key,
  group_id    bigint not null,
  paid_by     bigint not null,
  amount      numeric(12, 2) not null check (amount > 0),
  description text not null,
  unique (id, group_id),
  foreign key (group_id, paid_by) references members (group_id, user_id)
);

create table shares (
  expense_id bigint not null,
  group_id   bigint not null,
  user_id    bigint not null,
  amount     numeric(12, 2) not null check (amount >= 0),
  primary key (expense_id, user_id),
  foreign key (expense_id, group_id) references expenses (id, group_id) on delete cascade,
  foreign key (group_id, user_id) references members (group_id, user_id)
);

create table settlements (
  id       bigint generated always as identity primary key,
  group_id bigint not null,
  from_id  bigint not null,
  to_id    bigint not null,
  amount   numeric(12, 2) not null check (amount > 0),
  check (from_id <> to_id),
  foreign key (group_id, from_id) references members (group_id, user_id),
  foreign key (group_id, to_id) references members (group_id, user_id)
);

create function shares_add_up() returns trigger language plpgsql as $$
begin
  if (select amount from expenses where id = new.expense_id)
     <> (select sum(amount) from shares where expense_id = new.expense_id) then
    raise exception 'shares of expense % do not add up', new.expense_id;
  end if;
  return null;
end $$;
create constraint trigger shares_sum after insert on shares
  deferrable initially deferred for each row execute function shares_add_up();

-- balances filter by group: index the membership FKs
create index expenses_group_payer_idx on expenses (group_id, paid_by);
create index shares_group_user_idx on shares (group_id, user_id);
create index settlements_from_idx on settlements (group_id, from_id);
create index settlements_to_idx on settlements (group_id, to_id);
