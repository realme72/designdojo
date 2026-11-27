# Subscription Billing

> **Interview questions** (tab next to Problem): start there.

Design subscriptions and invoicing for a SaaS product (**PostgreSQL 17**).

## Requirements

1. **Plans** have a unique code and a monthly price. **Customers** have a unique email.
2. A **subscription** links a customer to a plan from a start time until an end time (open-ended
   while active). A customer never has **two subscriptions active at the same moment**; a new
   one may start exactly when the previous one ends.
3. **Cancelling** sets the end time (after the start). **Changing plan** ends the current
   subscription at that moment and starts a new one on the new plan at the same moment.
4. **Invoices** bill one subscription for one monthly period at the plan's price at that
   time. Billing the same subscription and period twice is rejected (retries must not
   double-charge).

## Operations

| Operation | Returns |
|---|---|
| `add_plan(:code, :monthly_price)`, `add_customer(:email)` | one row: `id` |
| `subscribe(:customer_id, :plan_code, :start_at)` | one row: `subscription_id` |
| `cancel(:subscription_id, :end_at)` | nothing |
| `change_plan(:subscription_id, :plan_code, :at)` | one row: `subscription_id` (the new one) |
| `bill(:subscription_id, :period_start)` | one row: `amount` |
| `mrr(:at)` | a single value: sum of monthly prices of subscriptions active at `:at` (0 if none) |
| `churned(:from, :to)` | rows `email`: customers whose subscription ended in `[from, to)` and who have nothing active at `:to`, by email |
