<script lang="ts">
	import { cyphertap } from 'cyphertap';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { sidebar } from '$lib/stores/sidebar.svelte.js';
	import WelcomePage from '$lib/components/WelcomePage.svelte';
	import ChatContainer from '$lib/components/chat/ChatContainer.svelte';
	import ThreadSidebar from '$lib/components/sidebar/ThreadSidebar.svelte';
	import { cn } from '$lib/utils.js';

	// Show welcome page if:
	// 1. User is not logged in, OR
	// 2. No agent is selected
	let showWelcome = $derived(!cyphertap.isLoggedIn || !$selectedAgent);
</script>

{#if showWelcome}
	<WelcomePage />
{:else}
	<ThreadSidebar />
	<!-- Main content wrapper that adjusts for sidebar on desktop -->
	<div
		class={cn(
			'transition-[margin-left] duration-200 ease-in-out',
			// On desktop, add left margin when sidebar is open (md: prefix handles mobile)
			sidebar.desktopOpen && 'md:ml-72'
		)}
	>
		<ChatContainer />
	</div>
{/if}
