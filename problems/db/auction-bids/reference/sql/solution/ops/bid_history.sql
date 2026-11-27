select u.name as bidder, b.amount from bids b join users u on u.id = b.bidder_id
where b.item_id = :item_id order by b.amount desc, b.id;
