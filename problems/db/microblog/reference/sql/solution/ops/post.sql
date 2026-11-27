with t as (
  insert into tweets (user_id, body, posted_at, reply_to)
  values (:user_id, :body, :posted_at, :reply_to)
  returning id, body
),
found as (
  select distinct lower(m[1]) as name from t, regexp_matches(t.body, '#(\w+)', 'g') as m
),
new_tags as (
  insert into tags (name) select name from found on conflict (name) do nothing returning id, name
),
all_tags as (
  select id, name from new_tags
  union
  select g.id, g.name from tags g join found f on f.name = g.name
),
linked as (
  insert into tweet_tags (tweet_id, tag_id) select t.id, a.id from t cross join all_tags a returning tweet_id
)
select id from t;
