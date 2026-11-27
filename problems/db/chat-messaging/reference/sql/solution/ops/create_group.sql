with conv as (insert into conversations (kind, name) values ('GROUP', :name) returning id),
m as (insert into members (conversation_id, user_id) select id, :owner_id from conv)
select id as conversation_id from conv;
