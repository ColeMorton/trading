/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,js}'],
  corePlugins: {
    preflight: true,
  },
  theme: {
    extend: {
      colors: {
        indigo: {
          600: '#6366f1',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          700: '#374151',
        },
      },
    },
  },
  plugins: [],
}