with q as (
  insert into questions (user_id, title, asked_at)
  select :user_id, :title, :asked_at
  where cardinality(:tags::text[]) between 1 and 5
  union all
  select :user_id, null, :asked_at   -- wrong number of tags: refuse
  where coalesce(cardinality(:tags::text[]), 0) not between 1 and 5
  returning id
),
names as (select distinct t from unnest(:tags::text[]) as t),
new_tags as (insert into tags (name) select t from names on conflict (name) do nothing returning id, name),
all_tags as (select id, name from new_tags union select g.id, g.name from tags g join names n on n.t = g.name),
link as (insert into question_tags (question_id, tag_id) select q.id, a.id from q cross join all_tags a)
select id from q;
