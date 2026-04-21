"""
tailwind.config.js - Tailwind CSS configuration for frontend
"""
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0f172a',
          light: '#f1f5f9',
        }
      }
    },
  },
  plugins: [],
}
