<script lang="ts">
	import { Cyphertap, cyphertap } from 'cyphertap';
	import 'cyphertap/styles.css';
	import AgentDropdown from './AgentDropdown.svelte';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { Zap } from '@lucide/svelte';
</script>

<nav class="sticky top-0 z-50 border-b border-[var(--color-border-default)] bg-[var(--color-bg-primary)]/80 backdrop-blur-md">
	<div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
		<!-- Left side: Logo and Agent Dropdown -->
		<div class="flex items-center gap-3">
			<a href="/" class="flex items-center gap-2 text-[var(--color-text-primary)] hover:text-[var(--color-cyan-glow)] transition-colors">
				<Zap class="h-6 w-6 text-[var(--color-cyan-glow)]" />
				<span class="text-xl font-semibold tracking-tight">PlebChat</span>
			</a>
			
			<span class="text-[var(--color-text-muted)]">/</span>
			
			<AgentDropdown />
		</div>

		<!-- Right side: CypherTap Component -->
		<div class="flex items-center gap-4">
			{#if cyphertap.isLoggedIn}
				<div class="hidden sm:flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
					<span class="text-[var(--color-cyan-glow)] font-mono">{cyphertap.balance}</span>
					<span>sats</span>
				</div>
			{/if}
			<Cyphertap />
		</div>
	</div>
</nav>
