import { useEffect, useRef, useState } from "react";

interface Props {
  text: string;
  label?: string;
  align?: "left" | "right";
}

/**
 * Small ⓘ icon that reveals a short description. Opens on hover (desktop) and
 * on tap (touch); tapping/clicking outside dismisses it.
 */
export default function InfoTip({ text, label = "More info", align = "left" }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <span
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen((o) => !o);
        }}
        className="flex h-4 w-4 items-center justify-center rounded-full border border-edge font-mono text-[9px] leading-none text-ash transition-colors hover:border-lime/60 hover:text-lime"
      >
        i
      </button>
      {open && (
        <span
          role="tooltip"
          className={`absolute bottom-full z-50 mb-1.5 w-52 rounded-md border border-edge bg-coal/95 p-2.5 font-mono text-[11px] leading-relaxed text-bone shadow-hud backdrop-blur ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {text}
        </span>
      )}
    </span>
  );
}
