<script lang="ts">
	import type { ToolCall } from '$lib/stores/threads.js';
	import { cn } from '$lib/utils.js';
	import { Wrench, Check, AlertCircle } from '@lucide/svelte';

	interface Props {
		toolCall: ToolCall;
	}

	let { toolCall }: Props = $props();
	let isExpanded = $state(false);
</script>

<div class="rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-tertiary)] overflow-hidden">
	<button
		onclick={() => isExpanded = !isExpanded}
		class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-[var(--color-bg-elevated)] transition-colors"
	>
		<Wrench class="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
		<span class="flex-1 font-mono text-xs text-[var(--color-text-secondary)]">
			{toolCall.name}
		</span>
		{#if toolCall.result}
			<Check class="w-3.5 h-3.5 text-[var(--color-green-success)]" />
		{:else}
			<AlertCircle class="w-3.5 h-3.5 text-[var(--color-amber-warning)]" />
		{/if}
	</button>

	{#if isExpanded}
		<div class="border-t border-[var(--color-border-default)] p-3 space-y-2">
			<div>
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Arguments</div>
				<pre class="text-xs font-mono text-[var(--color-text-secondary)] bg-[var(--color-bg-primary)] p-2 rounded overflow-x-auto">{JSON.stringify(toolCall.args, null, 2)}</pre>
			</div>
			{#if toolCall.result}
				<div>
					<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Result</div>
					<pre class="text-xs font-mono text-[var(--color-text-secondary)] bg-[var(--color-bg-primary)] p-2 rounded overflow-x-auto max-h-40">{toolCall.result}</pre>
				</div>
			{/if}
		</div>
	{/if}
</div>
