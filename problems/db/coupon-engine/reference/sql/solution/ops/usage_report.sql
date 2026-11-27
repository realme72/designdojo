select c.code, c.uses, coalesce(sum(r.discount), 0) as total_discount
from coupons c left join redemptions r on r.coupon_id = c.id
group by c.id, c.code, c.uses
order by c.code;
