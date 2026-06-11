import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { Alert } from "./Alert";

describe("Alert", () => {
  it("shows the error message when a message is provided", () => {
    renderWithProviders(<Alert message="Something went wrong" />);

    expect(screen.getByTestId("alert-message")).toHaveTextContent("Something went wrong");
  });
});
