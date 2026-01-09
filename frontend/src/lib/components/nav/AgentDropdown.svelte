<script lang="ts">
	import { selectedAgent, AGENTS, type Agent } from '$lib/stores/agent.js';
	import { ChevronDown, Check, Lock, HelpCircle } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';

	let isOpen = $state(false);
	let buttonRef = $state<HTMLButtonElement | null>(null);

	function selectAgent(agent: Agent) {
		if (agent.available) {
			selectedAgent.select(agent);
			isOpen = false;
		}
	}

	function handleClickOutside(event: MouseEvent) {
		if (buttonRef && !buttonRef.contains(event.target as Node)) {
			const dropdown = document.getElementById('agent-dropdown');
			if (dropdown && !dropdown.contains(event.target as Node)) {
				isOpen = false;
			}
		}
	}

	function goToHelp() {
		isOpen = false;
		selectedAgent.clear();
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="relative">
	<button
		bind:this={buttonRef}
		onclick={() => isOpen = !isOpen}
		class={cn(
			"flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all select-none",
			"border border-[var(--color-border-default)]",
			"hover:border-[var(--color-border-hover)] hover:bg-[var(--color-bg-elevated)]",
			"text-sm font-medium"
		)}
	>
		{#if $selectedAgent}
			<span>{$selectedAgent.emoji}</span>
			<span class="text-[var(--color-text-primary)]">{$selectedAgent.name}</span>
		{:else}
			<HelpCircle class="h-4 w-4 text-[var(--color-text-muted)]" />
			<span class="text-[var(--color-text-secondary)]">Select an agent</span>
		{/if}
		<ChevronDown class={cn(
			"h-4 w-4 text-[var(--color-text-muted)] transition-transform",
			isOpen && "rotate-180"
		)} />
	</button>

	{#if isOpen}
		<div
			id="agent-dropdown"
			class="absolute left-0 top-full mt-2 w-72 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] shadow-xl animate-fade-in z-50"
		>
			<div class="p-2">
				<!-- Help me choose option -->
				<button
					onclick={goToHelp}
					class={cn(
						"w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
						"hover:bg-[var(--color-bg-elevated)]",
						!$selectedAgent && "bg-[var(--color-bg-elevated)]"
					)}
				>
					<span class="text-lg">🤔</span>
					<div class="flex-1 text-left">
						<div class="text-sm font-medium text-[var(--color-text-primary)]">Help me choose</div>
						<div class="text-xs text-[var(--color-text-muted)]">View agent comparison</div>
					</div>
					{#if !$selectedAgent}
						<Check class="h-4 w-4 text-[var(--color-cyan-glow)]" />
					{/if}
				</button>

				<div class="my-2 border-t border-[var(--color-border-default)]"></div>

				<!-- Agent list -->
				{#each AGENTS as agent}
					<button
						onclick={() => selectAgent(agent)}
						disabled={!agent.available}
						class={cn(
							"w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
							agent.available && "hover:bg-[var(--color-bg-elevated)] cursor-pointer",
							!agent.available && "opacity-50 cursor-not-allowed",
							$selectedAgent?.id === agent.id && "bg-[var(--color-bg-elevated)]"
						)}
					>
						<span class="text-lg">{agent.emoji}</span>
						<div class="flex-1 text-left">
							<div class="flex items-center gap-2">
								<span class="text-sm font-medium text-[var(--color-text-primary)]">{agent.name}</span>
								{#if !agent.available}
									<Lock class="h-3 w-3 text-[var(--color-text-muted)]" />
								{/if}
							</div>
							<div class="text-xs text-[var(--color-text-muted)]">
								{agent.initialCost} sats
								{#if agent.additionalCost > 0}
									<span class="text-[var(--color-text-muted)]">• +{agent.additionalCost}/prompt</span>
								{/if}
							</div>
						</div>
						{#if $selectedAgent?.id === agent.id}
							<Check class="h-4 w-4 text-[var(--color-cyan-glow)]" />
						{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
