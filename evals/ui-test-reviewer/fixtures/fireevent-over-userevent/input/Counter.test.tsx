import { describe, it, expect } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { Counter } from "./Counter";

describe("Counter", () => {
  it("increments the count when the increment button is clicked", () => {
    renderWithProviders(<Counter />);

    fireEvent.click(screen.getByRole("button", { name: "Increment" }));

    expect(screen.getByRole("status")).toHaveTextContent("1");
  });
});
