select (select count(*) from seats st join shows sh on sh.screen_id = st.screen_id where sh.id = :show_id)
     - (select count(*) from booked_seats where show_id = :show_id);
