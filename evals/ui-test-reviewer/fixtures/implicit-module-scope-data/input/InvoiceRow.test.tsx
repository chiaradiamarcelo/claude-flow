import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { InvoiceRow } from "./InvoiceRow";

const invoice = {
  id: "INV-1",
  customer: "Ada Lovelace",
  amountCents: 12_345,
  currency: "USD",
  dueDate: "2026-07-01",
  status: "OPEN",
};

describe("InvoiceRow", () => {
  it("formats the amount as currency when the invoice is rendered", () => {
    renderWithProviders(<InvoiceRow invoice={invoice} />);

    expect(screen.getByRole("cell", { name: "$123.45" })).toBeInTheDocument();
  });
});
