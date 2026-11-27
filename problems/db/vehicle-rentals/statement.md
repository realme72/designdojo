# Vehicle Rentals (Zoomcar)

> **Interview questions** (tab next to Problem): start there.

Design a car-rental database (**PostgreSQL 17**).

## Requirements

1. **Vehicles** have a unique plate, a category (`HATCH`, `SEDAN`, `SUV`) and a daily rate.
   **Customers** have a unique licence number and a name.
2. A **rental** books one vehicle for whole days `[from_day, to_day)` (at least one day). A
   vehicle's active rentals never overlap. Cancelled rentals free the vehicle.
3. Reserving picks the free vehicle of the category with the lowest plate.
4. On **return**, the customer reports kilometres driven: 200 km per day are free, beyond that
   8.00 per km. The charge (days × rate + extra km) is stored with the rental.

## Operations

| Operation | Returns |
|---|---|
| `add_vehicle(:plate, :category, :daily_rate)` | one row: `id` |
| `add_customer(:licence, :name)` | one row: `id` |
| `reserve(:customer_id, :category, :from_day, :to_day)` | one row: `rental_id`, `plate` |
| `cancel(:rental_id)` | nothing |
| `return_vehicle(:rental_id, :km)` | one row: `charge` |
| `utilization(:from_day, :to_day)` | rows `plate`, `days`: active rental days falling inside `[from_day, to_day)` per vehicle (0 if none), by plate |
