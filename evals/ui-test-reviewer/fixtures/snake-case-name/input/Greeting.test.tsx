import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { Greeting } from "./Greeting";

describe("Greeting", () => {
  it("renders_the_user_name_when_a_name_is_provided", () => {
    renderWithProviders(<Greeting name="Ada" />);

    expect(screen.getByRole("heading")).toHaveTextContent("Hello, Ada");
  });
});
