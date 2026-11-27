insert into folders (owner_id, parent_id, name) values (:owner_id, :parent_id, :name) returning id;
