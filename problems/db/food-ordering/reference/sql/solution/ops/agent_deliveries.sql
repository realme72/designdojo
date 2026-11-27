select a.name as agent, count(o.id) as delivered
from agents a left join orders o on o.agent_id = a.id and o.status = 'DELIVERED'
group by a.id, a.name order by a.name;
