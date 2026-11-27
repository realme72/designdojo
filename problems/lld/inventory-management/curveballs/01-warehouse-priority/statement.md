# Warehouse priority

Shipping from the nearest warehouse is cheaper. `set_priority(warehouse, priority)`: lower
numbers are drawn from first. Warehouses with a priority come before those without; ties
(and warehouses without one) go in name order, as before.

*Interviewer's question:* did you change the allocation strategy, or add one?
