<script lang="ts">
	import '../app.css';
	import { Toaster } from 'svelte-sonner';
	import Navbar from '$lib/components/nav/Navbar.svelte';
	import MouseTrail from '$lib/components/effects/MouseTrail.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<title>PlebChat - AI Chat with Bitcoin Micropayments</title>
	<link rel="icon" href="/favicon.svg" />
</svelte:head>

<div class="bg-digital min-h-screen flex flex-col">
	<Navbar />
	<main class="flex-1 relative z-10">
		{@render children()}
	</main>
</div>

<MouseTrail />
<Toaster 
	theme="dark" 
	position="bottom-right"
	toastOptions={{
		style: 'background: var(--color-bg-elevated); border: 1px solid var(--color-border-default); color: var(--color-text-primary);'
	}}
/>
