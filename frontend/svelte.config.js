import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		// Static adapter for pure client-side SPA
		// All routes fall back to index.html for client-side routing
		adapter: adapter({
			fallback: 'index.html',
			strict: false
		})
	}
};

export default config;
