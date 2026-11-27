with recursive tree as (
  select id, body, 0 as depth, array[row_number() over ()]::bigint[] as path, posted_at
  from tweets where id = :tweet_id
  union all
  select c.id, c.body, p.depth + 1,
         p.path || row_number() over (partition by c.reply_to order by c.posted_at, c.id),
         c.posted_at
  from tweets c join tree p on c.reply_to = p.id
)
select id, depth, body from tree order by path;
