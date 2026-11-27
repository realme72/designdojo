with l as (
  select id, url from links
  where code = :code and (expires_at is null or expires_at > :at) and created_at <= :at
),
c as (insert into clicks (link_id, clicked_at, country) select id, :at, :country from l)
select url from l;
