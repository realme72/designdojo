with e as (
  insert into expenses (group_id, paid_by, amount, description)
  values (:group_id, :paid_by, :amount, :description) returning id, group_id, amount
),
p as (
  select u.user_id, u.ord, count(*) over () as n
  from unnest(:participants::int[]) with ordinality as u(user_id, ord)
),
s as (
  insert into shares (expense_id, group_id, user_id, amount)
  select e.id, e.group_id, p.user_id,
         ((round(e.amount * 100)::bigint / p.n) + case when p.ord <= (round(e.amount * 100)::bigint % p.n) then 1 else 0 end) / 100.0
  from e, p
)
select id from e;
