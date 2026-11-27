insert into books (isbn, title) values (:isbn, :title) returning id;
