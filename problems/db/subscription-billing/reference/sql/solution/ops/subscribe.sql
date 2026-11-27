insert into subscriptions (customer_id, plan_id, start_at)
select :customer_id, (select id from plans where code = :plan_code), :start_at
returning id as subscription_id;
