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

  it("renders the ref label when present, index as fallback", () => {
    render(
      <BoxOverlay
        width={100}
        height={100}
        boxes={[
          { x1: 0, y1: 0, x2: 10, y2: 10, label: "person" },
          { x1: 20, y1: 20, x2: 30, y2: 30 },
        ]}
        points={[]}
      />,
    );
    expect(screen.getByText("person")).toBeInTheDocument();
    expect(screen.getByText("02")).toBeInTheDocument();
  });

  it("sets a title attribute carrying the full label text", () => {
    render(
      <BoxOverlay
        width={100}
        height={100}
        boxes={[{ x1: 0, y1: 0, x2: 10, y2: 10, label: "people wearing red shirts" }]}
        points={[]}
      />,
    );
    expect(screen.getByText("people wearing red shirts")).toHaveAttribute(
      "title",
      "people wearing red shirts",
    );
  });

  it("labels a point with its ref text", () => {
    render(
      <BoxOverlay width={100} height={100} boxes={[]} points={[{ x: 50, y: 50, label: "cat" }]} />,
    );
    expect(screen.getByText("cat")).toBeInTheDocument();
  });
});
