/**
 * PostCSS Configuration (Phase 0)
 *
 * PostCSS is a tool for transforming CSS with JavaScript plugins.
 * This configuration enables:
 * - Tailwind CSS processing
 * - Autoprefixer for browser compatibility
 *
 * References:
 * - https://postcss.org/
 * - https://tailwindcss.com/docs/installation/using-postcss
 * - https://github.com/postcss/autoprefixer
 */
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
