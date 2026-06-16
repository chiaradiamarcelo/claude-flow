import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/renderWithProviders";
import { ProfileCard } from "./ProfileCard";

describe("ProfileCard", () => {
  it("shows the display name when a user is provided", () => {
    renderWithProviders(
      <ProfileCard user={{ name: "Ada", role: "Admin", avatarUrl: "/a.png" }} theme="light" />,
    );

    expect(screen.getByRole("heading", { name: "Ada" })).toBeInTheDocument();
  });

  it("shows the role label when a user is provided", () => {
    renderWithProviders(
      <ProfileCard user={{ name: "Ada", role: "Admin", avatarUrl: "/a.png" }} theme="light" />,
    );

    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("renders the avatar image when a user is provided", () => {
    renderWithProviders(
      <ProfileCard user={{ name: "Ada", role: "Admin", avatarUrl: "/a.png" }} theme="light" />,
    );

    expect(screen.getByRole("img", { name: "Ada" })).toHaveAttribute("src", "/a.png");
  });
});
