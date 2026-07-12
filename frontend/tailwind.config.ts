import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#fcfcfb",
          dark: "#1a1a19",
        },
        plane: {
          DEFAULT: "#f9f9f7",
          dark: "#0d0d0d",
        },
        ink: {
          primary: "#0b0b0b",
          "primary-dark": "#ffffff",
          secondary: "#52514e",
          "secondary-dark": "#c3c2b7",
          muted: "#898781",
        },
        line: {
          hairline: "#e1e0d9",
          "hairline-dark": "#2c2c2a",
          baseline: "#c3c2b7",
          "baseline-dark": "#383835",
        },
        series: {
          1: "#2a78d6",
          2: "#1baf7a",
          3: "#eda100",
          4: "#008300",
          5: "#4a3aa7",
          6: "#e34948",
          7: "#e87ba4",
          8: "#eb6834",
        },
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          serious: "#ec835a",
          critical: "#d03b3b",
        },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
