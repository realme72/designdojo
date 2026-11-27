select g.name as tag, count(*) as tweets
from tweet_tags tt
join tweets t on t.id = tt.tweet_id
join tags g on g.id = tt.tag_id
where t.posted_at >= :since
group by g.name
order by tweets desc, g.name
limit :n;
