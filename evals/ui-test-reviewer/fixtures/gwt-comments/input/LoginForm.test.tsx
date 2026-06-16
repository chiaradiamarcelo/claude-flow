import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/renderWithProviders";
import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("submits the entered credentials when the form is submitted", async () => {
    // Given
    const user = userEvent.setup();
    const onLogin = vi.fn();
    renderWithProviders(<LoginForm onLogin={onLogin} />);
    // When
    await user.type(screen.getByRole("textbox", { name: "Email" }), "ada@example.com");
    await user.click(screen.getByRole("button", { name: "Log in" }));
    // Then
    expect(onLogin).toHaveBeenCalledWith("ada@example.com");
  });
});
