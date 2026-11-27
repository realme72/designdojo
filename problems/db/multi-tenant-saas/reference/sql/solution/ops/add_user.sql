insert into users (tenant_id, email) values (:tenant_id, :email) returning id;
