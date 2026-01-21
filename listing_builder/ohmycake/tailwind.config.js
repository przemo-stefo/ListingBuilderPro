/**
 * location: ohmycake/tailwind.config.js
 * Purpose: Tailwind CSS configuration for Oh My Cake - custom colors matching brand identity
 * NOT for: Runtime configuration (this is for build process, CDN uses inline config)
 *
 * To use with Tailwind CLI (production):
 * 1. npm install -D tailwindcss
 * 2. npx tailwindcss -i ./src/input.css -o ./dist/output.css --minify
 */

module.exports = {
    content: ['./*.html'],
    theme: {
        extend: {
            colors: {
                // Updated to match Oh My Cake logo colors
                cream: '#FFF8F3',
                'cream-dark': '#FFF0E8',
                'pastel-pink': '#F5B5AC',
                'pastel-pink-dark': '#EFAAA0',
                'accent-pink': '#E8967D',
                'accent-pink-dark': '#D4847A',
                'soft-rose': '#FFF5F0',
                'warm-white': '#FFFBF8',
                'coral': {
                    100: '#FFF0E8',
                    200: '#FDDCD2',
                    300: '#F5B5AC',
                    400: '#E8A095',
                    500: '#E8967D',
                    600: '#D4847A',
                    700: '#C07068',
                },
            },
            fontFamily: {
                poppins: ['Poppins', 'sans-serif'],
            },
            animation: {
                'fade-in': 'fadeIn 0.6s ease-out forwards',
                'slide-up': 'slideUp 0.6s ease-out forwards',
                'scale-in': 'scaleIn 0.4s ease-out forwards',
                'float': 'float 3s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(30px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                scaleIn: {
                    '0%': { opacity: '0', transform: 'scale(0.95)' },
                    '100%': { opacity: '1', transform: 'scale(1)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
            },
        },
    },
    plugins: [],
};
