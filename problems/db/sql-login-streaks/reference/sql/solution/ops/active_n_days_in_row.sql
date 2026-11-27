with days as (select distinct user_id, (logged_at at time zone 'UTC')::date as d from logins),
islands as (select user_id, d - (row_number() over (partition by user_id order by d))::int as grp from days),
runs as (select user_id, count(*) as len from islands group by user_id, grp)
select u.name from users u where exists (select 1 from runs r where r.user_id = u.id and r.len >= :n)
order by u.name;
