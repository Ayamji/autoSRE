/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#0f172a',
        darker: '#020617',
        card: '#1e293b',
        border: '#334155'
      }
    },
  },
  plugins: [],
}
