import type { Box } from "../api/types";

/** Length of a reticle corner bracket for a box, in image-pixel units. */
export function bracketLength(box: Box): number {
  const w = Math.abs(box.x2 - box.x1);
  const h = Math.abs(box.y2 - box.y1);
  return Math.max(6, Math.min(Math.min(w, h) * 0.22, 36));
}

/**
 * SVG path `d` strings for the four "L"-shaped corner brackets of a targeting
 * reticle drawn around `box`. Returned in order: TL, TR, BR, BL.
 */
export function cornerBrackets(box: Box, len = bracketLength(box)): string[] {
  const { x1, y1, x2, y2 } = box;
  return [
    `M ${x1} ${y1 + len} L ${x1} ${y1} L ${x1 + len} ${y1}`,
    `M ${x2 - len} ${y1} L ${x2} ${y1} L ${x2} ${y1 + len}`,
    `M ${x2} ${y2 - len} L ${x2} ${y2} L ${x2 - len} ${y2}`,
    `M ${x1 + len} ${y2} L ${x1} ${y2} L ${x1} ${y2 - len}`,
  ];
}

export function boxArea(box: Box): number {
  return Math.abs(box.x2 - box.x1) * Math.abs(box.y2 - box.y1);
}
