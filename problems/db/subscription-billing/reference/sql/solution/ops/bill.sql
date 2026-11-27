insert into invoices (subscription_id, period_start, amount)
select s.id, :period_start, p.monthly_price from subscriptions s join plans p on p.id = s.plan_id where s.id = :subscription_id
returning amount;
