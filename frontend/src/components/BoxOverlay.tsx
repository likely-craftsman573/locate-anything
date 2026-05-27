import { motion } from "framer-motion";

import type { Box, Point } from "../api/types";
import { cornerBrackets } from "../lib/geometry";

interface Props {
  width: number;
  height: number;
  boxes: Box[];
  points: Point[];
  showLabels?: boolean;
}

const STROKE = "#c6f432";
const POINT = "#ff9d3d";

export default function BoxOverlay({ width, height, boxes, points, showLabels = true }: Props) {
  return (
    <div className="pointer-events-none absolute inset-0">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full"
        data-testid="overlay-svg"
      >
        {boxes.map((b, i) => (
          <g key={`b${i}`} data-testid="overlay-box">
            <motion.rect
              x={Math.min(b.x1, b.x2)}
              y={Math.min(b.y1, b.y2)}
              width={Math.abs(b.x2 - b.x1)}
              height={Math.abs(b.y2 - b.y1)}
              fill="rgba(198,244,50,0.07)"
              stroke="rgba(198,244,50,0.35)"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15 + i * 0.07, duration: 0.3 }}
            />
            {cornerBrackets(b).map((d, c) => (
              <motion.path
                key={c}
                d={d}
                fill="none"
                stroke={STROKE}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ delay: i * 0.07, duration: 0.4, ease: "easeOut" }}
              />
            ))}
          </g>
        ))}

        {points.map((p, i) => (
          <motion.g
            key={`p${i}`}
            data-testid="overlay-point"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            style={{ transformOrigin: `${p.x}px ${p.y}px` }}
          >
            <circle cx={p.x} cy={p.y} r={9} fill="none" stroke={POINT} strokeWidth={2} vectorEffect="non-scaling-stroke" />
            <line x1={p.x - 16} y1={p.y} x2={p.x + 16} y2={p.y} stroke={POINT} strokeWidth={2} vectorEffect="non-scaling-stroke" />
            <line x1={p.x} y1={p.y - 16} x2={p.x} y2={p.y + 16} stroke={POINT} strokeWidth={2} vectorEffect="non-scaling-stroke" />
          </motion.g>
        ))}
      </svg>

      {showLabels &&
        boxes.map((b, i) => (
          <span
            key={`l${i}`}
            className="absolute -translate-y-full bg-lime px-1.5 py-0.5 font-mono text-[10px] font-semibold leading-none text-ink"
            style={{
              left: `${(Math.min(b.x1, b.x2) / width) * 100}%`,
              top: `${(Math.min(b.y1, b.y2) / height) * 100}%`,
            }}
          >
            {String(i + 1).padStart(2, "0")}
          </span>
        ))}
    </div>
  );
}
