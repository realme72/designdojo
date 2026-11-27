# Food Delivery (Swiggy / Zomato)

Design the order flow of a food-delivery platform: menus, orders, restaurant acceptance,
delivery-agent assignment and customer notifications.

## Requirements

1. `add_restaurant(id)`, `add_item(restaurant, item_id, price)` (items start available),
   `set_item_available(restaurant, item_id, available)`, `add_agent(agent_id)`.
   Unknown restaurant/item → `UnknownRestaurant` / `UnknownItem`.
2. `place_order(customer, restaurant, lines)`: each line is `{item_id, qty}`. Empty order or
   `qty < 1` → `InvalidOrder`; unavailable item → `ItemUnavailable`.
   `total = Σ price × qty + delivery_fee` (config). Status `PLACED`.
3. Lifecycle (anything else → `InvalidState`):
   `PLACED → ACCEPTED` (`accept`) or `REJECTED` (`reject`);
   `ACCEPTED → READY` (`mark_ready`); `READY → OUT_FOR_DELIVERY` (`pick_up`, needs an agent);
   `OUT_FOR_DELIVERY → DELIVERED` (`deliver`); `PLACED`/`ACCEPTED → CANCELLED` (`cancel`).
4. **Agents**: on `accept`, the free agent with the lowest id is assigned. If none is free,
   the order waits; when an agent becomes free (delivery, or cancellation of their order)
   they are assigned to the **oldest waiting** order that's still active.
5. **Notifications**: every status change appends `"<order_id>:<STATUS>"` to the customer's
   notifications (including `PLACED`). `notifications(customer)` returns them in order.
6. `order(id)` returns the order; `free_agents()` counts idle agents; `waiting_orders()`
   counts accepted/ready orders without an agent. Unknown order → `UnknownOrder`.
7. Restaurants accept orders concurrently: an agent never carries two orders at once.

## Things an interviewer will push on

- How would you add SMS/push channels for notifications without touching the order code?
- Where does the agent-assignment strategy live (nearest, least busy)?
- What does the state machine look like, and who is allowed to trigger each transition?
