insert into files (folder_id, name, size_bytes) values (:folder_id, :name, :size_bytes) returning id;
