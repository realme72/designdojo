select l.code, count(c.id) as clicks
from links l left join clicks c on c.link_id = l.id
where l.owner = :owner group by l.id, l.code order by clicks desc, l.code limit :n;
