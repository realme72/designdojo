select count(distinct a.user_id) from activity a
where date_trunc('month', a.active_on) = :month::date
  and exists (select 1 from activity p where p.user_id = a.user_id
              and date_trunc('month', p.active_on) = (:month::date - interval '1 month'));
