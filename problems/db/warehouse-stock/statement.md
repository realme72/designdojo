# Multi-Warehouse Stock

> **Interview questions** (tab next to Problem): start there.

Design inventory tracking across warehouses (**PostgreSQL 17**).

## Requirements

1. **Products** have a unique SKU; **warehouses** a unique code.
2. Stock is kept per (warehouse, product) and can never be negative.
3. Every change is a **movement** with a reason: `RECEIVE`, `SHIP` or `TRANSFER` (a transfer is
   two movements: out of one warehouse, into another, together). Quantities are positive.
   Movements are an append-only history, and current stock always equals the sum of movements.
4. Shipping or transferring more than is available is rejected and changes nothing.

## Operations

| Operation | Returns |
|---|---|
| `add_product(:sku)`, `add_warehouse(:code)` | one row: `id` |
| `receive(:warehouse_id, :product_id, :qty)` | nothing |
| `ship(:warehouse_id, :product_id, :qty)` | nothing |
| `transfer(:from_id, :to_id, :product_id, :qty)` | nothing |
| `stock_by_warehouse(:product_id)` | rows `warehouse`, `qty`: warehouses that have ever held it, by code |
| `low_stock(:threshold)` | rows `sku`, `total`: every product whose total across warehouses is below the threshold (including never-stocked products, total 0), by sku |
| `history(:product_id)` | rows `warehouse`, `change`, `reason`: movements in order (signed change) |
