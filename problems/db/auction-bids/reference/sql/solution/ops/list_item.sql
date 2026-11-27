insert into items (seller_id, title, start_price, ends_at) values (:seller_id, :title, :start_price, :ends_at) returning id;
