# SCENARIO-01: Shipping fee for a completed order

## Scenario

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

## Structure & Contracts

- **Domain / calculation:** the fee rule is pure computation over `(subtotal, region, itemCount)`. No persistence, no external lookup — region and subtotal arrive in the request.
- **Use case:** `CalculateShippingFee` (`application/`) — the behavioural entry point; takes the order's subtotal, item count, and destination region and returns the fee. No ports (nothing to read or write).
- **API:** `POST /shipping-quote` → `200` with the computed fee; `400` on malformed body / missing required field (subtotal, region).
