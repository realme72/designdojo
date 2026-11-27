insert into messages (conversation_id, sender_id, body, sent_at) values (:conversation_id, :sender_id, :body, :sent_at) returning id;
