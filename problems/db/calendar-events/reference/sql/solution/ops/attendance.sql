select response, count(*) as people from attendees where event_id = :event_id group by response order by response;
