create table accounts (
  id       bigint generated always as identity primary key,
  owner    text not null,
  kind     text not null default 'WALLET' check (kind in ('WALLET', 'EXTERNAL')),
  balance  numeric(14, 2) not null default 0,
  check (kind = 'EXTERNAL' or balance >= 0)        -- wallets never go negative
);
insert into accounts (owner, kind) values ('external deposits', 'EXTERNAL');

create table transactions (
  id              bigint generated always as identity primary key,
  kind            text not null check (kind in ('DEPOSIT', 'TRANSFER')),
  idempotency_key text not null unique,
  created_at      timestamptz not null default now()
);

create table entries (
  id         bigint generated always as identity primary key,
  txn_id     bigint not null references transactions (id),
  account_id bigint not null references accounts (id),
  amount     numeric(14, 2) not null check (amount <> 0)
);
create index entries_txn_idx on entries (txn_id);
create index entries_account_idx on entries (account_id, txn_id);

-- every transaction balances, checked at commit time
create function check_balanced() returns trigger language plpgsql as $$
begin
  if (select coalesce(sum(amount), 0) from entries where txn_id = new.txn_id) <> 0 then
    raise exception 'transaction % does not balance', new.txn_id;
  end if;
  return null;
end $$;
create constraint trigger entries_balanced after insert on entries
  deferrable initially deferred for each row execute function check_balanced();

-- append-only history
create function reject_change() returns trigger language plpgsql as $$
begin raise exception 'ledger entries are append-only'; end $$;
create trigger entries_append_only before update or delete on entries for each row execute function reject_change();
