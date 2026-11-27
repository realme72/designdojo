insert into videos (channel_id, title, duration_s, visibility, uploaded_at) values (:channel_id, :title, :duration_s, :visibility, :uploaded_at) returning id;
