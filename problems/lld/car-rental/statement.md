# Car Rental (Zoomcar)

Design a car rental system. Dates are **day numbers**; today is `clock.now() // 86400`.

## Requirements

1. `add_car(car_id, branch, category, daily_rate, odometer)`; repeated id → `DuplicateCar`.
2. A rental covers days `[pickup_day, return_day)`. `return_day ≤ pickup_day` or
   `pickup_day` before today → `InvalidDates`.
3. `available(branch, category, pickup_day, return_day)` → free car ids, sorted.
   `reserve(customer, branch, category, pickup_day, return_day)` takes the lowest free car
   id and returns `{id, car_id, status}` with status `RESERVED`. None → `NoCarAvailable`.
4. `pick_up(rental_id)`: only `RESERVED`, and only on or after `pickup_day` →
   else `InvalidState`. The rental becomes `ACTIVE`; the car's odometer is recorded.
5. `return_car(rental_id, odometer)`: only `ACTIVE`; `odometer` below the recorded start →
   `InvalidOdometer`. Returns the bill `{base, late_fee, mileage_fee, total}`:
   - `base = booked days × daily_rate`
   - `late_fee = max(0, today − return_day) × daily_rate × late_multiplier` (config)
   - `mileage_fee = max(0, km driven − free_km_per_day × booked days) × per_km` (config)
   The rental becomes `RETURNED` and the car's odometer is updated. A late car stays
   unavailable until it is returned.
6. `cancel(rental_id)`: only `RESERVED` (else `InvalidState`). Unknown rental → `UnknownRental`.
7. Customers reserve concurrently: a car is never double-booked.

## Things an interviewer will push on

- Where does pricing live (weekend rates, insurance add-ons)?
- How would one-way rentals (return at another branch) change availability?
- Model the rental lifecycle: which transitions are legal?
