update members set last_read_id = greatest(last_read_id, :message_id)
where conversation_id = :conversation_id and user_id = :user_id;
