select c.country, count(*) as clicks, round(100.0 * count(*) / sum(count(*)) over (), 1) as share
from clicks c join links l on l.id = c.link_id
where l.code = :code group by c.country order by clicks desc, c.country;
