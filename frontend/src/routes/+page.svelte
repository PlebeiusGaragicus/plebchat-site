<script lang="ts">
	import { cyphertap } from 'cyphertap';
	import { selectedAgent } from '$lib/stores/agent.js';
	import WelcomePage from '$lib/components/WelcomePage.svelte';
	import ChatContainer from '$lib/components/chat/ChatContainer.svelte';
	import ThreadSidebar from '$lib/components/sidebar/ThreadSidebar.svelte';
	import { browser } from '$app/environment';

	// Sidebar state - persisted in localStorage
	let sidebarOpen = $state(false);

	// Load sidebar state on mount
	$effect(() => {
		if (browser) {
			const stored = localStorage.getItem('plebchat-sidebar-open');
			if (stored !== null) {
				sidebarOpen = stored === 'true';
			}
		}
	});

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
		if (browser) {
			localStorage.setItem('plebchat-sidebar-open', String(sidebarOpen));
		}
	}

	// Show welcome page if:
	// 1. User is not logged in, OR
	// 2. No agent is selected
	let showWelcome = $derived(!cyphertap.isLoggedIn || !$selectedAgent);
</script>

{#if showWelcome}
	<WelcomePage />
{:else}
	<ThreadSidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
	<ChatContainer />
{/if}
