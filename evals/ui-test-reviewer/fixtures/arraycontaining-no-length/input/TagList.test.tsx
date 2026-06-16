import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { TagList } from "./TagList";

describe("TagList", () => {
  it("renders a chip for each provided tag", () => {
    renderWithProviders(<TagList tags={["react", "testing"]} />);

    const labels = screen.getAllByRole("listitem").map((node) => node.textContent);
    expect(labels).toEqual(expect.arrayContaining(["react", "testing"]));
  });
});
