<script lang="ts">
	import { Cyphertap } from 'cyphertap';
	import 'cyphertap/styles.css';
	import AgentDropdown from './AgentDropdown.svelte';
	import { TESTING_MODE } from '$lib/stores/stream.svelte.js';
	import { Zap, FlaskConical } from '@lucide/svelte';
</script>

<nav class="sticky top-0 z-50 border-b border-[var(--color-border-default)] bg-[var(--color-bg-primary)]/80 backdrop-blur-md">
	<div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-3 sm:px-4">
		<!-- Left side: Logo and Agent Dropdown -->
		<div class="flex items-center gap-2 sm:gap-3">
			<a href="/" class="flex items-center gap-1.5 sm:gap-2 text-[var(--color-text-primary)] hover:text-[var(--color-cyan-glow)] transition-colors">
				<Zap class="h-5 w-5 sm:h-6 sm:w-6 text-[var(--color-cyan-glow)]" />
				<span class="hidden sm:inline text-lg sm:text-xl font-semibold tracking-tight">PlebChat</span>
			</a>
			
			<span class="hidden sm:inline text-[var(--color-text-muted)] select-none">/</span>
			
			<div class="select-none">
				<AgentDropdown />
			</div>
		</div>

		<!-- Right side: Testing Mode and CypherTap Component -->
		<div class="flex items-center gap-2 sm:gap-4">
			{#if TESTING_MODE}
				<div class="flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-full bg-[var(--color-amber-warning)]/20 border border-[var(--color-amber-warning)]/50">
					<FlaskConical class="w-3 h-3 text-[var(--color-amber-warning)]" />
					<span class="hidden sm:inline text-[10px] sm:text-xs text-[var(--color-amber-warning)] font-medium">
						Test
					</span>
				</div>
			{/if}
			<Cyphertap />
		</div>
	</div>
</nav>
