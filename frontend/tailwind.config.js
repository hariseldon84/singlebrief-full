/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: false,
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Theme colors
        background: 'rgb(var(--background))',
        foreground: 'rgb(var(--foreground))',
        card: 'rgb(var(--card))',
        'card-foreground': 'rgb(var(--card-foreground))',
        border: 'rgb(var(--border))',
        input: 'rgb(var(--input))',
        ring: 'rgb(var(--ring))',
        muted: 'rgb(var(--muted))',
        'muted-foreground': 'rgb(var(--muted-foreground))',
        accent: 'rgb(var(--accent))',
        'accent-foreground': 'rgb(var(--accent-foreground))',
        
        // SingleBrief Brand Colors
        // SingleBrief Brand Colors
        primary: {
          DEFAULT: '#1A2D64', // Primary Blue
          50: '#f0f2f8',
          100: '#e1e6f1',
          200: '#c4cde3',
          300: '#a6b4d5',
          400: '#899bc7',
          500: '#6b82b9',
          600: '#5a6fa1',
          700: '#4a5c89',
          800: '#394971',
          900: '#1A2D64', // Primary Blue
          950: '#0f1832',
        },
        highlight: {
          DEFAULT: '#F57C00', // Highlight Orange
          50: '#fef7ed',
          100: '#fdedd5',
          200: '#fbd7aa',
          300: '#f9bc74',
          400: '#f6973c',
          500: '#F57C00', // Highlight Orange
          600: '#e76200',
          700: '#c14d02',
          800: '#9a3e08',
          900: '#7c340a',
        },
        soft: {
          DEFAULT: '#FFE3C3', // Soft Orange
          50: '#fefcf9',
          100: '#fef6ed',
          200: '#fdead5',
          300: '#fcd9b3',
          400: '#FAC291',
          500: '#FFE3C3', // Soft Orange
          600: '#f5b567',
          700: '#eb9234',
          800: '#d4741a',
          900: '#b05e15',
        },
        neutral: {
          DEFAULT: '#6B7280', // Neutral Gray
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6B7280', // Neutral Gray
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        success: {
          DEFAULT: '#2BAE66', // Success Green
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#2BAE66', // Success Green
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Satoshi', 'Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '8px',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
      spacing: {
        // 8px spacing system
        '0.5': '2px',
        '1': '4px',
        '1.5': '6px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
        '20': '80px',
        '24': '96px',
        '32': '128px',
      },
      boxShadow: {
        'soft': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'medium': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'large': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}