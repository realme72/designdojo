with t as (
  insert into transactions (kind, idempotency_key)
  select 'TRANSFER', :key where :amount::numeric > 0 and :from_id::bigint <> :to_id::bigint
  union all
  select 'TRANSFER', null where not (:amount::numeric > 0 and :from_id::bigint <> :to_id::bigint)
  on conflict (idempotency_key) do nothing
  returning id
),
e as (
  insert into entries (txn_id, account_id, amount)
  select t.id, x.account_id, x.amount from t,
    (values (:from_id::bigint, -:amount::numeric), (:to_id::bigint, :amount::numeric)) as x(account_id, amount)
),
debit as (   -- CHECK (balance >= 0) rejects overdrafts; the row lock serializes concurrent debits
  update accounts set balance = balance - :amount::numeric
  where id = :from_id and kind = 'WALLET' and exists (select 1 from t) returning id
),
credit as (
  update accounts set balance = balance + :amount::numeric
  where id = :to_id and kind = 'WALLET' and exists (select 1 from t) returning id
)
select id as txn_id from t
union all
select id from transactions where idempotency_key = :key and not exists (select 1 from t);
