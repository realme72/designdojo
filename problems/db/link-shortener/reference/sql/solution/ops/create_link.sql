insert into links (code, url, owner, created_at, expires_at) values (:code, :url, :owner, :created_at, :expires_at) returning id;
