with old as (
  update subscriptions set end_at = :at where id = :subscription_id and end_at is null and start_at < :at
  returning customer_id
)
insert into subscriptions (customer_id, plan_id, start_at)
select old.customer_id, (select id from plans where code = :plan_code), :at from old
union all
select null, null, :at where not exists (select 1 from old)   -- nothing active to change: refuse
returning id as subscription_id;
