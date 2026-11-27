with r as (
  update loans set returned_at = :at
  where copy_id = (select id from copies where barcode = :barcode) and returned_at is null
  returning due_at
)
select greatest(0, ceil(extract(epoch from (:at::timestamptz - due_at)) / 86400)) * 10.00 as fine from r;
