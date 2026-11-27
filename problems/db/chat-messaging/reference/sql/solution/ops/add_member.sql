insert into members (conversation_id, user_id)
select id, :user_id from conversations where id = :conversation_id and kind = 'GROUP'
union all
select :conversation_id, null where not exists (select 1 from conversations where id = :conversation_id and kind = 'GROUP');
