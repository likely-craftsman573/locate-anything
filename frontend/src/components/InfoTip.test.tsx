import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import InfoTip from "./InfoTip";

describe("InfoTip", () => {
  it("toggles the description on click and dismisses on outside click", () => {
    render(
      <div>
        <InfoTip text="Helpful description" />
        <button>outside</button>
      </div>,
    );

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "More info" }));
    expect(screen.getByRole("tooltip")).toHaveTextContent("Helpful description");

    fireEvent.mouseDown(screen.getByRole("button", { name: "outside" }));
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
