# Surge pricing

Rain in the city. `set_surge(vehicle, percent)` multiplies fares for that vehicle class:
`fare × percent / 100` (rounded down). The surge in force **when the ride is requested** is the
one the rider pays, even if it changes before the trip ends. `100` means no surge;
`percent < 100` raises `InvalidSurge`.

*Interviewer's question:* decorator over the pricing strategy, or a field on the trip?
