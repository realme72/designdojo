# Parcel Tracking

> **Interview questions** (tab next to Problem): start there.

Design shipment tracking for a courier (**PostgreSQL 17**).

## Requirements

1. A **shipment** has a unique tracking number, origin and destination cities and a creation
   time; it starts in status `CREATED` at the origin.
2. **Scans** are an append-only history: status, location and time. Allowed moves:
   `CREATED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED`; `IN_TRANSIT → IN_TRANSIT`
   (hub to hub) and `OUT_FOR_DELIVERY → IN_TRANSIT` (failed attempt) are allowed too. Nothing
   follows `DELIVERED`. A scan can't be earlier than the shipment's previous event.
3. The **current status** is the latest event.

## Operations

| Operation | Returns |
|---|---|
| `create_shipment(:tracking_no, :origin, :destination, :at)` | one row: `id` |
| `scan(:tracking_no, :status, :location, :at)` | nothing |
| `track(:tracking_no)` | rows `status`, `location`, `at`: full history including creation, oldest first |
| `current(:tracking_no)` | one row: `status`, `location` |
| `stuck(:at, :hours)` | rows `tracking_no`, `status`: undelivered shipments whose latest event is more than `:hours` before `:at`, by tracking number |
| `avg_delivery_hours(:origin, :destination)` | a single value: average hours from creation to delivery on that lane, 1 decimal (NULL if none) |
