with avgs as (
  select p.category, p.name, avg(r.rating) as a
  from products p join reviews r on r.product_id = p.id
  group by p.id, p.category, p.name having count(*) >= :min_reviews
),
ranked as (select *, rank() over (partition by category order by a desc) as rk from avgs)
select category, name, round(a, 2) as avg_rating from ranked where rk = 1 order by category, name;
