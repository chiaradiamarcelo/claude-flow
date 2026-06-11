import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/renderWithProviders";
import { SubmitButton } from "./SubmitButton";

describe("SubmitButton", () => {
  it("Should call onSubmit when the button is clicked", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    renderWithProviders(<SubmitButton onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(onSubmit).toHaveBeenCalledOnce();
  });
});
