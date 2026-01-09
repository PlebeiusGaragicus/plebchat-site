<script lang="ts">
	import type { ThreadMessage } from '$lib/stores/threads.js';
	import { cn } from '$lib/utils.js';
	import { User, Bot, Wrench, ChevronDown, ChevronUp } from '@lucide/svelte';
	import ToolCallDisplay from './ToolCallDisplay.svelte';

	interface Props {
		message: ThreadMessage;
		isStreaming?: boolean;
	}

	let { message, isStreaming = false }: Props = $props();
	let showToolCalls = $state(false);
</script>

<div class={cn(
	"flex gap-3 px-4 py-4 animate-fade-in",
	message.type === 'human' && "bg-transparent",
	message.type === 'ai' && "bg-[var(--color-bg-secondary)]/50"
)}>
	<!-- Avatar -->
	<div class={cn(
		"flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center",
		message.type === 'human' && "bg-[var(--color-purple-dim)]",
		message.type === 'ai' && "bg-gradient-to-br from-[var(--color-cyan-glow)] to-[var(--color-cyan-dim)]",
		message.type === 'tool' && "bg-[var(--color-bg-elevated)]"
	)}>
		{#if message.type === 'human'}
			<User class="w-4 h-4 text-white" />
		{:else if message.type === 'ai'}
			<Bot class="w-4 h-4 text-[var(--color-bg-primary)]" />
		{:else}
			<Wrench class="w-4 h-4 text-[var(--color-text-muted)]" />
		{/if}
	</div>

	<!-- Content -->
	<div class="flex-1 min-w-0">
		<div class="flex items-center gap-2 mb-1">
			<span class={cn(
				"text-sm font-medium",
				message.type === 'human' && "text-[var(--color-purple-accent)]",
				message.type === 'ai' && "text-[var(--color-cyan-glow)]",
				message.type === 'tool' && "text-[var(--color-text-muted)]"
			)}>
				{message.type === 'human' ? 'You' : message.type === 'ai' ? 'PlebChat' : 'Tool'}
			</span>
			{#if isStreaming}
				<span class="inline-flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
					<span class="w-1.5 h-1.5 bg-[var(--color-cyan-glow)] rounded-full animate-pulse"></span>
					Thinking...
				</span>
			{/if}
		</div>

		<div class="text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap break-words">
			{message.content}
			{#if isStreaming && !message.content}
				<span class="inline-block w-2 h-4 bg-[var(--color-cyan-glow)] animate-pulse"></span>
			{/if}
		</div>

		<!-- Tool calls -->
		{#if message.toolCalls && message.toolCalls.length > 0}
			<button
				onclick={() => showToolCalls = !showToolCalls}
				class="mt-3 flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
			>
				{#if showToolCalls}
					<ChevronUp class="w-3 h-3" />
				{:else}
					<ChevronDown class="w-3 h-3" />
				{/if}
				{message.toolCalls.length} tool call{message.toolCalls.length > 1 ? 's' : ''}
			</button>

			{#if showToolCalls}
				<div class="mt-2 space-y-2">
					{#each message.toolCalls as toolCall}
						<ToolCallDisplay {toolCall} />
					{/each}
				</div>
			{/if}
		{/if}
	</div>
</div>
