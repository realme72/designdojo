# Sticky sessions

Logged-in users should keep hitting the same server (their session lives there). Add
`acquire_for(client_id)`: the first call picks a server with the current strategy and remembers
it; later calls return the same server while it exists and is healthy. If it was removed or is
unhealthy, pick again with the strategy and remember the new one. Counts toward `active` like
`acquire`.

*Interviewer's question:* is stickiness another strategy, or a layer over any strategy?
