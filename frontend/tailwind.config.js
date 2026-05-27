/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: "#0a0c08", // near-black backdrop
        coal: "#10130c", // elevated surface
        panel: "#161a10", // panels / cards
        edge: "#272d1d", // borders
        bone: "#e9ecdd", // primary text
        ash: "#8b9377", // muted text
        lime: "#c6f432", // primary accent — bounding boxes
        amber: "#ff9d3d", // signal — points
        rose: "#ff5470", // danger / delete
      },
      fontFamily: {
        display: ['"Archivo Expanded"', '"Archivo"', "sans-serif"],
        sans: ['"Archivo"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        hud: "0 0 0 1px rgba(198,244,50,0.12), 0 24px 60px -28px rgba(0,0,0,0.9)",
        glow: "0 0 24px -4px rgba(198,244,50,0.45)",
      },
      keyframes: {
        sweep: {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateY(100%)", opacity: "0" },
        },
        blink: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.25" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        sweep: "sweep 1.1s cubic-bezier(0.4,0,0.2,1)",
        blink: "blink 1.4s ease-in-out infinite",
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};
