insert into menu_items (restaurant_id, name, price) values (:restaurant_id, :name, :price) returning id;
