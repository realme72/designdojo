insert into copies (book_id, barcode) values (:book_id, :barcode) returning id;
