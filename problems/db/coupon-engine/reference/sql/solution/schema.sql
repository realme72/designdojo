create table coupons (
  id          bigint generated always as identity primary key,
  code        text not null,
  percent_off int check (percent_off between 1 and 100),
  flat_off    numeric(10, 2) check (flat_off > 0),
  min_order   numeric(10, 2) not null default 0 check (min_order >= 0),
  max_uses    int not null check (max_uses > 0),
  per_user    int not null check (per_user > 0),
  valid_from  timestamptz not null,
  valid_to    timestamptz not null,
  uses        int not null default 0,
  check (num_nonnulls(percent_off, flat_off) = 1),     -- exactly one kind of discount
  check (valid_to > valid_from),
  check (uses between 0 and max_uses)                    -- global limit, race-free
);
create unique index coupons_code_lower_key on coupons (lower(code));

create table coupon_user_uses (
  coupon_id bigint not null references coupons (id),
  user_id   bigint not null,
  uses      int not null check (uses >= 1),
  primary key (coupon_id, user_id)
);

create table redemptions (
  id          bigint generated always as identity primary key,
  coupon_id   bigint not null references coupons (id),
  user_id     bigint not null,
  order_total numeric(10, 2) not null check (order_total > 0),
  discount    numeric(10, 2) not null check (discount >= 0),
  redeemed_at timestamptz not null
);
create index redemptions_coupon_idx on redemptions (coupon_id);

create function per_user_limit() returns trigger language plpgsql as $$
begin
  if new.uses > (select per_user from coupons where id = new.coupon_id) then
    raise exception 'per-user limit reached';
  end if;
  return new;
end $$;
create trigger coupon_user_uses_limit before insert or update on coupon_user_uses for each row execute function per_user_limit();
