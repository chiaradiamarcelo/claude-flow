import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/renderWithProviders";
import { SearchBox } from "./SearchBox";

describe("SearchBox", () => {
  it("calls onSearch with the query and clears the input when submitted", async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    renderWithProviders(<SearchBox onSearch={onSearch} />);

    const input = screen.getByRole("searchbox");
    await user.type(input, "laptops");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(onSearch).toHaveBeenCalledWith("laptops");
    expect(input).toHaveValue("");
  });
});
