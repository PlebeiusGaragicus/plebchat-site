<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { Send, Settings, Loader2, AlertTriangle } from '@lucide/svelte';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { currentThread } from '$lib/stores/threads.js';

	interface Props {
		onSubmit: (message: string) => void;
		isLoading?: boolean;
		disabled?: boolean;
		balance?: number;
		onOpenSettings?: () => void;
	}

	let { onSubmit, isLoading = false, disabled = false, balance = 0, onOpenSettings }: Props = $props();
	
	let message = $state('');
	let textareaRef = $state<HTMLTextAreaElement | null>(null);

	function handleSubmit(e?: Event) {
		e?.preventDefault();
		if (!message.trim() || isLoading || disabled || hasInsufficientBalance) return;
		onSubmit(message.trim());
		message = '';
		// Reset textarea height
		if (textareaRef) {
			textareaRef.style.height = 'auto';
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function autoResize() {
		if (!textareaRef) return;
		textareaRef.style.height = 'auto';
		textareaRef.style.height = Math.min(textareaRef.scrollHeight, 150) + 'px';
	}

	// Calculate cost for current prompt - always uses full agent pricing
	let promptCost = $derived.by(() => {
		if (!$selectedAgent) return 0;
		const thread = $currentThread;
		if (!thread || thread.promptCount === 0) {
			return $selectedAgent.initialCost;
		}
		return $selectedAgent.additionalCost;
	});

	// Check if user has insufficient balance
	let hasInsufficientBalance = $derived($selectedAgent && balance < promptCost);
</script>

<form onsubmit={handleSubmit} class="relative">
	<!-- Low balance warning -->
	{#if hasInsufficientBalance}
		<div class="absolute -top-10 sm:-top-12 left-0 right-0 flex items-center justify-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400">
			<AlertTriangle class="w-3.5 h-3.5 flex-shrink-0" />
			<span class="text-[10px] sm:text-xs">
				Low balance: you need <span class="font-semibold">{promptCost}</span> sats but only have <span class="font-semibold">{balance}</span> sats
			</span>
		</div>
	{/if}

	<!-- Input container -->
	<div class={cn(
		"glow-input rounded-full sm:rounded-[2rem] p-1 sm:p-1.5 overflow-hidden",
		hasInsufficientBalance && "border-amber-500/50"
	)}>
		<div class="flex items-end gap-1 sm:gap-2">
			<!-- Text input area -->
			<textarea
				bind:this={textareaRef}
				bind:value={message}
				onkeydown={handleKeyDown}
				oninput={autoResize}
				placeholder={hasInsufficientBalance ? "Add funds to continue..." : ($selectedAgent ? "Ask me anything..." : "Select an agent first")}
				disabled={disabled || !$selectedAgent}
				rows={1}
				class={cn(
					"flex-1 resize-none bg-transparent px-3 sm:px-5 py-3 sm:py-4 text-sm sm:text-base text-[var(--color-text-primary)]",
					"placeholder:text-[var(--color-text-muted)]",
					"focus:outline-none focus:ring-0",
					"disabled:opacity-50 disabled:cursor-not-allowed",
					"max-h-[150px] min-h-[48px] sm:min-h-[56px]"
				)}
			></textarea>

			<!-- Action buttons -->
			<div class="flex items-center gap-1 pb-2 sm:pb-3 pr-2 sm:pr-3 flex-shrink-0">
				<!-- Settings button - always visible -->
				{#if $selectedAgent && onOpenSettings}
					<button
						type="button"
						onclick={onOpenSettings}
						class={cn(
							"flex p-2 rounded-full transition-colors",
							"text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]",
							"hover:bg-[var(--color-bg-elevated)]"
						)}
						title="Agent settings"
					>
						<Settings class="w-4 h-4 sm:w-5 sm:h-5" />
					</button>
				{/if}

				<!-- Send button -->
				<button
					type="submit"
					disabled={!message.trim() || isLoading || disabled || !$selectedAgent || hasInsufficientBalance}
					class={cn(
						"p-2 sm:p-3 rounded-full transition-all",
						"bg-gradient-to-r from-[var(--color-accent-primary)] to-[var(--color-accent-dim)]",
						"text-black font-medium",
						"hover:shadow-[var(--shadow-glow-sm)]",
						"disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
					)}
				>
					{#if isLoading}
						<Loader2 class="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
					{:else}
						<Send class="w-4 h-4 sm:w-5 sm:h-5" />
					{/if}
				</button>
			</div>
		</div>
	</div>

	<!-- Cost indicator (only show when not showing low balance warning) -->
	{#if $selectedAgent && message.trim() && !hasInsufficientBalance}
		<div class="absolute -top-6 sm:-top-8 right-2 sm:right-0 text-[10px] sm:text-xs text-[var(--color-text-muted)]">
			<span class="text-[var(--color-accent-primary)]">{promptCost}</span> sats
		</div>
	{/if}
</form>

