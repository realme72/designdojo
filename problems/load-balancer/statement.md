# Load Balancer

Design an in-process load balancer that picks a backend server for each request.

## Requirements

1. `add_server(id, weight)` (`weight < 1` → `InvalidWeight`, repeated → `DuplicateServer`);
   `remove_server(id)`; `set_healthy(id, healthy)`. Servers start healthy. Unknown →
   `UnknownServer`. Server order is by id.
2. `acquire()` picks a **healthy** server, counts an active connection on it and returns
   its id; none healthy → `NoHealthyServer`. `release(id)` ends one connection
   (`InvalidState` if it has none). `active(id)` returns its active connections.
3. `set_strategy(strategy)` (default `ROUND_ROBIN`); switching resets the strategy's state.
   - `ROUND_ROBIN`: the next healthy server after the previously chosen one, in id order,
     wrapping around (the first pick is the first healthy server).
   - `WEIGHTED_ROUND_ROBIN`: smooth weighted round robin: on each pick, add each healthy
     server's weight to its running score, choose the highest score (ties → lowest id), then
     subtract the total healthy weight from the chosen one's score. Scores start at 0.
   - `LEAST_CONNECTIONS`: fewest active connections, ties → lowest id.
4. Requests arrive concurrently: selections and connection counts must stay consistent.

## Things an interviewer will push on

- How do you add a new algorithm (IP hash, least response time) without touching the balancer?
- Health checks: who calls set_healthy, and how often?
- Why "smooth" weighted round robin instead of repeating a server `weight` times in a row?
