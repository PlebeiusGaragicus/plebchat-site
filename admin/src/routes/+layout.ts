// Disable SSR - this is a client-side only admin app
// CypherTap requires browser APIs (localStorage, window, etc.)
export const ssr = false;

// Enable prerendering for static export
export const prerender = true;
