create table users (
  id     bigint generated always as identity primary key,
  handle text not null unique
);

create table tweets (
  id        bigint generated always as identity primary key,
  user_id   bigint not null references users (id),
  body      text not null check (length(body) between 1 and 280),
  posted_at timestamptz not null,
  reply_to  bigint references tweets (id)
);
create index tweets_user_idx on tweets (user_id);
create index tweets_reply_to_idx on tweets (reply_to);
create index tweets_posted_at_idx on tweets (posted_at);

create table tags (
  id   bigint generated always as identity primary key,
  name text not null unique check (name = lower(name))
);

create table tweet_tags (
  tweet_id bigint not null references tweets (id) on delete cascade,
  tag_id   bigint not null references tags (id),
  primary key (tweet_id, tag_id)
);
create index tweet_tags_tag_idx on tweet_tags (tag_id);

create table retweets (
  user_id  bigint not null references users (id),
  tweet_id bigint not null references tweets (id) on delete cascade,
  primary key (tweet_id, user_id)
);
create index retweets_user_idx on retweets (user_id);

-- "never your own tweet" needs the tweet's author: enforce it in the database
create function no_self_retweet() returns trigger language plpgsql as $$
begin
  if exists (select 1 from tweets t where t.id = new.tweet_id and t.user_id = new.user_id) then
    raise exception 'cannot retweet your own tweet';
  end if;
  return new;
end $$;
create trigger retweets_not_own before insert on retweets for each row execute function no_self_retweet();
