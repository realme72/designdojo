select count(*) from copies c join books b on b.id = c.book_id
where b.isbn = :isbn and not exists (select 1 from loans l where l.copy_id = c.id and l.returned_at is null);
