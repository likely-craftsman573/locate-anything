import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import BoxOverlay from "./BoxOverlay";

describe("BoxOverlay", () => {
  it("renders one group per box and per point with a matching viewBox", () => {
    render(
      <BoxOverlay
        width={640}
        height={480}
        boxes={[
          { x1: 10, y1: 10, x2: 100, y2: 100 },
          { x1: 200, y1: 50, x2: 300, y2: 150 },
        ]}
        points={[{ x: 320, y: 240 }]}
      />,
    );
    expect(screen.getAllByTestId("overlay-box")).toHaveLength(2);
    expect(screen.getAllByTestId("overlay-point")).toHaveLength(1);
    expect(screen.getByTestId("overlay-svg")).toHaveAttribute("viewBox", "0 0 640 480");
  });

  it("renders index labels when enabled", () => {
    render(
      <BoxOverlay width={100} height={100} boxes={[{ x1: 0, y1: 0, x2: 10, y2: 10 }]} points={[]} />,
    );
    expect(screen.getByText("01")).toBeInTheDocument();
  });
});
