import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/renderWithProviders";
import { PasswordField } from "./PasswordField";

describe("PasswordField", () => {
  it("reveals the password when the show button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PasswordField label="Password" />);

    await user.click(screen.getByRole("button", { name: "Show password" }));

    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "text");
  });
});
