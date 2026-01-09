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
	"flex gap-2 sm:gap-3 px-3 sm:px-4 py-3 sm:py-4 animate-fade-in",
	message.type === 'human' && "flex-row-reverse bg-transparent",
	message.type === 'ai' && "bg-[var(--color-bg-secondary)]/50"
)}>
	<!-- Avatar -->
	<div class={cn(
		"flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center",
		message.type === 'human' && "bg-[var(--color-purple-dim)]",
		message.type === 'ai' && "bg-gradient-to-br from-[var(--color-cyan-glow)] to-[var(--color-cyan-dim)]",
		message.type === 'tool' && "bg-[var(--color-bg-elevated)]"
	)}>
		{#if message.type === 'human'}
			<User class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
		{:else if message.type === 'ai'}
			<Bot class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--color-bg-primary)]" />
		{:else}
			<Wrench class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[var(--color-text-muted)]" />
		{/if}
	</div>

	<!-- Content -->
	<div class={cn(
		"flex-1 min-w-0",
		message.type === 'human' && "text-right"
	)}>
		<div class={cn(
			"flex items-center gap-2 mb-1",
			message.type === 'human' && "justify-end"
		)}>
			<span class={cn(
				"text-xs sm:text-sm font-medium",
				message.type === 'human' && "text-[var(--color-purple-accent)]",
				message.type === 'ai' && "text-[var(--color-cyan-glow)]",
				message.type === 'tool' && "text-[var(--color-text-muted)]"
			)}>
				{message.type === 'human' ? 'You' : message.type === 'ai' ? 'PlebChat' : 'Tool'}
			</span>
			{#if isStreaming}
				<span class="inline-flex items-center gap-1 text-[10px] sm:text-xs text-[var(--color-text-muted)]">
					<span class="w-1.5 h-1.5 bg-[var(--color-cyan-glow)] rounded-full animate-pulse"></span>
					Thinking...
				</span>
			{/if}
		</div>

		<div class={cn(
			"text-sm sm:text-base text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap break-words",
			message.type === 'human' && "inline-block text-left bg-[var(--color-purple-dim)]/20 rounded-2xl rounded-tr-sm px-3 py-2",
			message.type === 'ai' && "inline-block text-left bg-[var(--color-bg-elevated)] rounded-2xl rounded-tl-sm px-3 py-2"
		)}>
			{message.content}
			{#if isStreaming && !message.content}
				<span class="inline-block w-2 h-4 bg-[var(--color-cyan-glow)] animate-pulse"></span>
			{/if}
		</div>

		<!-- Tool calls -->
		{#if message.toolCalls && message.toolCalls.length > 0}
			<button
				onclick={() => showToolCalls = !showToolCalls}
				class="mt-2 sm:mt-3 flex items-center gap-1 text-[10px] sm:text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
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
