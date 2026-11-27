select lower(trim(email)) as email, count(*) as copies
from signups group by 1 having count(*) > 1 order by copies desc, email;
