with pair as (
  select least(:user_a::bigint, :user_b::bigint) as lo, greatest(:user_a::bigint, :user_b::bigint) as hi
),
existing as (
  select d.conversation_id from direct_pairs d, pair where d.user_low = pair.lo and d.user_high = pair.hi
),
conv as (
  insert into conversations (kind) select 'DIRECT' where not exists (select 1 from existing) returning id
),
pair_row as (
  insert into direct_pairs (conversation_id, user_low, user_high) select conv.id, pair.lo, pair.hi from conv, pair
  returning conversation_id
),
mem as (
  insert into members (conversation_id, user_id)
  select conv.id, u from conv, pair, unnest(array[pair.lo, pair.hi]) as u
)
select conversation_id from existing
union all
select conversation_id from pair_row;
