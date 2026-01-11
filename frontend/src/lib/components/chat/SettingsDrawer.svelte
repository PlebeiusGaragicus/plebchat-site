<script lang="ts">
	import type { Agent } from '$lib/stores/agent.js';
	import { Drawer } from 'vaul-svelte';
	import { Settings, X } from '@lucide/svelte';

	interface Props {
		open: boolean;
		agent: Agent | null;
	}

	let { open = $bindable(false), agent }: Props = $props();
</script>

<Drawer.Root bind:open direction="right">
	<Drawer.Portal>
		<Drawer.Overlay class="fixed inset-0 bg-black/50 z-40" />
		<Drawer.Content
			class="fixed right-0 top-0 bottom-0 z-50 w-[90vw] max-w-md bg-[var(--color-bg-secondary)] border-l border-[var(--color-border-hover)] outline-none flex flex-col"
		>
			<Drawer.Title class="sr-only">Agent Settings</Drawer.Title>
			<Drawer.Description class="sr-only">Configure agent settings for this session</Drawer.Description>

			<!-- Header -->
			<div
				class="flex items-center justify-between p-4 border-b border-[var(--color-border-hover)]"
			>
				<div class="flex items-center gap-3">
					<div
						class="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-dim)] flex items-center justify-center"
					>
						<Settings class="w-5 h-5 text-[var(--color-bg-primary)]" />
					</div>
					<div>
						<h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Agent Settings</h2>
						{#if agent}
							<p class="text-sm text-[var(--color-text-muted)]">{agent.name}</p>
						{/if}
					</div>
				</div>
				<Drawer.Close
					class="p-2 rounded-lg hover:bg-[var(--color-bg-elevated)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
				>
					<X class="w-5 h-5" />
				</Drawer.Close>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto overscroll-contain p-4">
				{#if agent}
					<!-- Agent Info -->
					<div
						class="p-4 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-border-hover)] mb-6"
					>
						<div class="flex items-center gap-3 mb-3">
							<span class="text-3xl">{agent.emoji}</span>
							<div>
								<h3 class="font-medium text-[var(--color-text-primary)]">{agent.name}</h3>
								<p class="text-sm text-[var(--color-text-muted)]">{agent.description}</p>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-3 text-sm">
							<div class="p-2 rounded bg-[var(--color-bg-secondary)]">
								<div class="text-[var(--color-text-muted)] text-xs">Initial Cost</div>
								<div class="text-[var(--color-accent-primary)] font-medium">{agent.initialCost} sats</div>
							</div>
							<div class="p-2 rounded bg-[var(--color-bg-secondary)]">
								<div class="text-[var(--color-text-muted)] text-xs">Per Prompt</div>
								<div class="text-[var(--color-accent-primary)] font-medium">
									{agent.additionalCost > 0 ? `+${agent.additionalCost} sats` : 'Free'}
								</div>
							</div>
						</div>
					</div>

					<!-- Settings placeholder -->
					<div class="space-y-4">
						<h4 class="text-sm font-medium text-[var(--color-text-primary)]">Configuration</h4>
						<div
							class="p-6 rounded-lg border border-dashed border-[var(--color-border-hover)] text-center"
						>
							<p class="text-[var(--color-text-muted)] text-sm">
								<em>Agent-specific settings coming soon...</em>
							</p>
							<p class="text-[var(--color-text-muted)] text-xs mt-2">
								Temperature, max tokens, system prompts, and more.
							</p>
						</div>
					</div>
				{:else}
					<div class="flex items-center justify-center h-full">
						<p class="text-[var(--color-text-muted)]">No agent selected</p>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="p-4 border-t border-[var(--color-border-hover)]">
				<Drawer.Close class="w-full btn btn-ghost">Close</Drawer.Close>
			</div>
		</Drawer.Content>
	</Drawer.Portal>
</Drawer.Root>
