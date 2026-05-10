import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0f0c",
        card: "#11181a",
        fg: "#d4e0d4",
        dim: "#6f8a73",
        accent: "#6ee07a",
        alert: "#e07a6e",
        border: "#1f2a26",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Source Code Pro", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
