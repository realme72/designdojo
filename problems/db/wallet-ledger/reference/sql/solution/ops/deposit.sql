with t as (
  insert into transactions (kind, idempotency_key)
  select 'DEPOSIT', :key where :amount::numeric > 0
  union all select 'DEPOSIT', null where not (:amount::numeric > 0)   -- non-positive amount: refuse
  on conflict (idempotency_key) do nothing
  returning id
),
e as (
  insert into entries (txn_id, account_id, amount)
  select t.id, x.account_id, x.amount from t,
    (values ((select id from accounts where kind = 'EXTERNAL'), -:amount::numeric), (:account_id::bigint, :amount::numeric)) as x(account_id, amount)
),
b as (
  update accounts set balance = balance + case when kind = 'EXTERNAL' then -:amount::numeric else :amount::numeric end
  where (id = :account_id or kind = 'EXTERNAL') and exists (select 1 from t)
)
select id as txn_id from t
union all
select id from transactions where idempotency_key = :key and not exists (select 1 from t);
