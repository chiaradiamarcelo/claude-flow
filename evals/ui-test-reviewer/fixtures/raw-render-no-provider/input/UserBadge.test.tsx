import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserBadge } from "./UserBadge";

describe("UserBadge", () => {
  it("displays the user initials when a full name is provided", () => {
    render(<UserBadge fullName="Ada Lovelace" />);

    expect(screen.getByRole("img", { name: "Ada Lovelace" })).toHaveTextContent("AL");
  });
});
