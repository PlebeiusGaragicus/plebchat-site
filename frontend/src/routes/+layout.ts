// Disable SSR - this is a pure client-side SPA
// No server rendering, everything runs in the browser
export const ssr = false;

// Prerender the HTML shell, client-side JS takes over at runtime
export const prerender = true;
