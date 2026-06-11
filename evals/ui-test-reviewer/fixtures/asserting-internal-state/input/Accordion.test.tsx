import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/renderWithProviders";
import { Accordion, useAccordionState } from "./Accordion";

describe("Accordion", () => {
  it("expands the panel when the header is clicked", async () => {
    const user = userEvent.setup();
    const setOpen = vi.fn();
    vi.spyOn(useAccordionState as never, "call");
    renderWithProviders(<Accordion title="Details" />);

    await user.click(screen.getByRole("button", { name: "Details" }));

    expect(setOpen).toHaveBeenCalledWith(true);
  });
});
