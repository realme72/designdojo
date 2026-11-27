create table users (id bigint generated always as identity primary key, name text not null);

create table conversations (
  id   bigint generated always as identity primary key,
  kind text not null check (kind in ('DIRECT', 'GROUP')),
  name text,
  check ((kind = 'GROUP') = (name is not null))
);

-- one direct conversation per unordered pair
create table direct_pairs (
  conversation_id bigint primary key references conversations (id),
  user_low        bigint not null references users (id),
  user_high       bigint not null references users (id),
  check (user_low < user_high),
  unique (user_low, user_high)
);
create index direct_pairs_high_idx on direct_pairs (user_high);

create table members (
  conversation_id bigint not null references conversations (id),
  user_id         bigint not null references users (id),
  last_read_id    bigint not null default 0,
  primary key (conversation_id, user_id)
);
create index members_user_idx on members (user_id);

create table messages (
  id              bigint generated always as identity primary key,
  conversation_id bigint not null,
  sender_id       bigint not null,
  body            text not null check (length(trim(body)) > 0),
  sent_at         timestamptz not null,
  foreign key (conversation_id, sender_id) references members (conversation_id, user_id)  -- members only
);
create index messages_conv_id_idx on messages (conversation_id, id);
