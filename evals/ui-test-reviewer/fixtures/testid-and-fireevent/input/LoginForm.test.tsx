import { render, fireEvent } from "@testing-library/react";
import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("ShouldSubmitTheForm", () => {
    const onSubmit = jest.fn();
    const { getByTestId } = render(<LoginForm onSubmit={onSubmit} />);
    fireEvent.change(getByTestId("email-input"), { target: { value: "a@b.com" } });
    fireEvent.click(getByTestId("submit-button"));
    expect(onSubmit).toHaveBeenCalled();
  });
});
