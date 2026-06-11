import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { CartSummary } from "./CartSummary";
import { priceService } from "./priceService";

vi.mock("./priceService");

let items: Array<{ sku: string; qty: number }>;

beforeEach(() => {
  vi.clearAllMocks();
  items = [
    { sku: "A", qty: 2 },
    { sku: "B", qty: 1 },
  ];
});

describe("CartSummary", () => {
  it("shows the total item count when the cart has items", () => {
    renderWithProviders(<CartSummary items={items} />);

    expect(screen.getByRole("status")).toHaveTextContent("3 items");
  });
});
