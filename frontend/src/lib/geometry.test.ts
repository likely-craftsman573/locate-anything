import { describe, expect, it } from "vitest";

import { bracketLength, cornerBrackets } from "./geometry";

describe("cornerBrackets", () => {
  it("produces four L-shaped corner paths", () => {
    const paths = cornerBrackets({ x1: 0, y1: 0, x2: 100, y2: 100 }, 10);
    expect(paths).toEqual([
      "M 0 10 L 0 0 L 10 0",
      "M 90 0 L 100 0 L 100 10",
      "M 100 90 L 100 100 L 90 100",
      "M 10 100 L 0 100 L 0 90",
    ]);
  });
});

describe("bracketLength", () => {
  it("clamps tiny boxes to a minimum", () => {
    expect(bracketLength({ x1: 0, y1: 0, x2: 4, y2: 4 })).toBe(6);
  });

  it("clamps huge boxes to a maximum", () => {
    expect(bracketLength({ x1: 0, y1: 0, x2: 9000, y2: 9000 })).toBe(36);
  });
});
