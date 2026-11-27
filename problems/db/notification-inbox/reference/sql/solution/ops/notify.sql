with ins as (
  insert into notifications (user_id, type, text, idempotency_key, created_at)
  select :user_id, :type, :text, :key, :created_at
  where not exists (select 1 from mutes where user_id = :user_id and type = :type)
  on conflict (user_id, idempotency_key) do nothing
  returning id
)
select id from ins
union all
select n.id from notifications n
where n.user_id = :user_id and n.idempotency_key = :key and not exists (select 1 from ins);
