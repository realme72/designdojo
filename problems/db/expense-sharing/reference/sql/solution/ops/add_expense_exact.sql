with e as (
  insert into expenses (group_id, paid_by, amount, description)
  values (:group_id, :paid_by, :amount, :description) returning id, group_id
),
s as (
  insert into shares (expense_id, group_id, user_id, amount)
  select e.id, e.group_id, (x ->> 'user_id')::bigint, (x ->> 'amount')::numeric
  from e, jsonb_array_elements(:shares) as x
)
select id from e;
