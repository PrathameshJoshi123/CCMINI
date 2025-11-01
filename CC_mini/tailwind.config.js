/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
      },
      typography: {
        DEFAULT: {
          css: {
            table: {
              'border-collapse': 'collapse',
              width: '100%',
              'margin-top': '1.5em',
              'margin-bottom': '1.5em',
            },
            'table thead tr': {
              'border-bottom': '1px solid #e5e7eb',
            },
            'table th': {
              border: '1px solid #d1d5db',
              'background-color': '#f3f4f6',
              padding: '0.75rem',
              'text-align': 'left',
              'font-weight': '600',
            },
            'table td': {
              border: '1px solid #d1d5db',
              padding: '0.75rem',
            },
            'table tbody tr:nth-child(even)': {
              'background-color': '#f9fafb',
            },
          },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
