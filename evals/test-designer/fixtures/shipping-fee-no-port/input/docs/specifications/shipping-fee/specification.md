# Feature: Shipping fee

## Intent

Compute the shipping fee a customer pays at checkout from the order's subtotal
and destination — cheap, deterministic, no I/O.

## Business rules

- Subtotal **below 50.00** → flat **5.00** shipping fee.
- Subtotal **50.00 or above** → **free** shipping (the 50.00 boundary ships free).
- An order to a **remote region** pays an extra **3.00 surcharge** on top of the
  subtotal-based fee, whatever that fee is (including on top of free shipping).
- An **empty order** (no items) pays **no fee at all** — not even a surcharge.

## BDD Acceptance Progress

- [ ] SCENARIO-01: Shipping fee for a completed order

## Scenarios

### SCENARIO-01

```gherkin
Scenario: Shipping fee is derived from order subtotal and destination
  Given an order with a subtotal and a destination region
  When the shipping fee is calculated
  Then an order subtotal below 50.00 pays a flat 5.00 shipping fee
  And an order subtotal of exactly 50.00 ships free
  And an order subtotal above 50.00 ships free
  And an order to a remote region pays an extra 3.00 surcharge on top of whatever the subtotal-based fee is
  And an empty order (no items) pays no shipping fee at all
```
