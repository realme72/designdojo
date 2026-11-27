with accepted as (   -- one conditional update: the item's row lock serializes concurrent bids
  update items set current_price = :amount, current_leader = :bidder_id
  where id = :item_id
    and :at::timestamptz < ends_at
    and seller_id <> :bidder_id
    and :amount::numeric >= coalesce(current_price + 1, start_price)
  returning id
)
insert into bids (item_id, bidder_id, amount, placed_at)
select :item_id, :bidder_id, :amount, :at from accepted
union all
select :item_id, :bidder_id, null, :at where not exists (select 1 from accepted)   -- refused
returning id as bid_id;
