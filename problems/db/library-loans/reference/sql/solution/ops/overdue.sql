select m.name as member, b.title, ceil(extract(epoch from (:at::timestamptz - l.due_at)) / 86400)::int as days_overdue
from loans l join members m on m.id = l.member_id join copies c on c.id = l.copy_id join books b on b.id = c.book_id
where l.returned_at is null and l.due_at < :at
order by days_overdue desc, m.name;
