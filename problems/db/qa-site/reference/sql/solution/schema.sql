create table users (id bigint generated always as identity primary key, name text not null unique);
create table tags (id bigint generated always as identity primary key, name text not null unique);

create table questions (
  id                 bigint generated always as identity primary key,
  user_id            bigint not null references users (id),
  title              text not null check (length(title) > 0),
  asked_at           timestamptz not null,
  accepted_answer_id bigint
);
create index questions_user_idx on questions (user_id);

create table question_tags (
  question_id bigint not null references questions (id) on delete cascade,
  tag_id      bigint not null references tags (id),
  primary key (question_id, tag_id)
);
create index question_tags_tag_idx on question_tags (tag_id);

create table answers (
  id          bigint generated always as identity primary key,
  question_id bigint not null references questions (id) on delete cascade,
  user_id     bigint not null references users (id),
  body        text not null,
  unique (question_id, id)
);
create index answers_user_idx on answers (user_id);

-- the accepted answer must be an answer to this question
alter table questions add foreign key (id, accepted_answer_id) references answers (question_id, id);

create table question_votes (
  user_id     bigint not null references users (id),
  question_id bigint not null references questions (id) on delete cascade,
  value       smallint not null check (value in (-1, 1)),
  primary key (question_id, user_id)
);
create index question_votes_user_idx on question_votes (user_id);

create table answer_votes (
  user_id   bigint not null references users (id),
  answer_id bigint not null references answers (id) on delete cascade,
  value     smallint not null check (value in (-1, 1)),
  primary key (answer_id, user_id)
);
create index answer_votes_user_idx on answer_votes (user_id);

create function no_self_vote() returns trigger language plpgsql as $$
declare author bigint;
begin
  if tg_table_name = 'question_votes' then
    select user_id into author from questions where id = new.question_id;
  else
    select user_id into author from answers where id = new.answer_id;
  end if;
  if author = new.user_id then raise exception 'cannot vote on your own post'; end if;
  return new;
end $$;
create trigger question_votes_not_own before insert or update on question_votes for each row execute function no_self_vote();
create trigger answer_votes_not_own before insert or update on answer_votes for each row execute function no_self_vote();
