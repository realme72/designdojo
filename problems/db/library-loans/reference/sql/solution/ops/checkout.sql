insert into loans (copy_id, member_id, loaned_at, due_at)
select (select id from copies where barcode = :barcode), :member_id, :at, :at::timestamptz + interval '14 days'
returning id as loan_id, due_at;
