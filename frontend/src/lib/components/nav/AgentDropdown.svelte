<script lang="ts">
	import { selectedAgent, AGENTS, type Agent } from '$lib/stores/agent.js';
	import { ChevronDown, Check, Lock, HelpCircle } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';
	import { DropdownMenu } from 'bits-ui';

	let open = $state(false);

	function selectAgent(agent: Agent) {
		if (agent.available) {
			selectedAgent.select(agent);
			open = false;
		}
	}

	function goToHelp() {
		selectedAgent.clear();
		open = false;
	}
</script>

<DropdownMenu.Root bind:open>
	<DropdownMenu.Trigger
		class={cn(
			'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all select-none',
			'border border-[var(--color-border-hover)]',
			'hover:border-[var(--color-border-bright)] hover:bg-[var(--color-bg-elevated)]',
			'text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]/50'
		)}
	>
		{#if $selectedAgent}
			<span>{$selectedAgent.emoji}</span>
			<span class="text-[var(--color-text-primary)]">{$selectedAgent.name}</span>
		{:else}
			<HelpCircle class="h-4 w-4 text-[var(--color-text-muted)]" />
			<span class="text-[var(--color-text-secondary)]">Select an agent</span>
		{/if}
		<ChevronDown
			class={cn(
				'h-4 w-4 text-[var(--color-text-muted)] transition-transform',
				open && 'rotate-180'
			)}
		/>
	</DropdownMenu.Trigger>

	<DropdownMenu.Portal>
		<DropdownMenu.Content
			class="z-50 w-72 rounded-xl border border-[var(--color-border-hover)] bg-[var(--color-bg-secondary)] p-2 shadow-xl animate-fade-in"
			sideOffset={8}
			align="start"
		>
			<!-- Help me choose option -->
			<DropdownMenu.Item
				class={cn(
					'flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer outline-none',
					'hover:bg-[var(--color-bg-elevated)] focus:bg-[var(--color-bg-elevated)]',
					!$selectedAgent && 'bg-[var(--color-bg-elevated)]'
				)}
				onSelect={goToHelp}
			>
				<span class="text-lg">🤔</span>
				<div class="flex-1">
					<div class="text-sm font-medium text-[var(--color-text-primary)]">Help me choose</div>
					<div class="text-xs text-[var(--color-text-muted)]">View agent comparison</div>
				</div>
				{#if !$selectedAgent}
					<Check class="h-4 w-4 text-[var(--color-accent-primary)]" />
				{/if}
			</DropdownMenu.Item>

			<DropdownMenu.Separator class="my-2 h-px bg-[var(--color-border-hover)]" />

			<!-- Agent list -->
			{#each AGENTS as agent}
				<DropdownMenu.Item
					disabled={!agent.available}
					class={cn(
						'flex items-center gap-3 px-3 py-2.5 rounded-lg outline-none',
						agent.available &&
							'cursor-pointer hover:bg-[var(--color-bg-elevated)] focus:bg-[var(--color-bg-elevated)]',
						!agent.available && 'opacity-50 cursor-not-allowed',
						$selectedAgent?.id === agent.id && 'bg-[var(--color-bg-elevated)]'
					)}
					onSelect={() => selectAgent(agent)}
				>
					<span class="text-lg">{agent.emoji}</span>
					<div class="flex-1">
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
						<Check class="h-4 w-4 text-[var(--color-accent-primary)]" />
					{/if}
				</DropdownMenu.Item>
			{/each}
		</DropdownMenu.Content>
	</DropdownMenu.Portal>
</DropdownMenu.Root>
