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
		<div class="absolute -top-12 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 bg-amber-500/15 border border-amber-500/40 rounded-full text-amber-400 backdrop-blur-sm whitespace-nowrap">
			<AlertTriangle class="w-3.5 h-3.5 flex-shrink-0" />
			<span class="text-[10px] sm:text-xs">
				Need <span class="font-semibold">{promptCost}</span> sats · have <span class="font-semibold">{balance}</span>
			</span>
		</div>
	{/if}

	<!-- Floating input container -->
	<div class={cn(
		"relative rounded-[2rem] sm:rounded-[2.5rem] overflow-hidden",
		"bg-[var(--color-bg-secondary)]/90 backdrop-blur-xl",
		"border border-[var(--color-border-hover)]",
		"shadow-[0_8px_32px_rgba(0,0,0,0.4),0_0_0_1px_rgba(255,255,255,0.03)_inset]",
		"transition-all duration-300",
		"hover:border-[var(--color-border-bright)] hover:shadow-[0_8px_40px_rgba(0,0,0,0.5),0_0_20px_rgba(249,115,22,0.08)]",
		"focus-within:border-[var(--color-accent-primary)]/50 focus-within:shadow-[0_8px_40px_rgba(0,0,0,0.5),0_0_30px_rgba(249,115,22,0.15)]",
		hasInsufficientBalance && "border-amber-500/40"
	)}>
		<div class="flex items-center">
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
					"flex-1 resize-none bg-transparent",
					"pl-5 sm:pl-7 pr-2 py-4 sm:py-5",
					"text-sm sm:text-base text-[var(--color-text-primary)]",
					"placeholder:text-[var(--color-text-muted)]",
					"focus:outline-none focus:ring-0",
					"disabled:opacity-50 disabled:cursor-not-allowed",
					"max-h-[150px] min-h-[52px] sm:min-h-[60px]"
				)}
			></textarea>

			<!-- Action buttons - vertically centered -->
			<div class="flex items-center gap-1.5 sm:gap-2 pr-2 sm:pr-3 flex-shrink-0">
				<!-- Settings button -->
				{#if $selectedAgent && onOpenSettings}
					<button
						type="button"
						onclick={onOpenSettings}
						class={cn(
							"flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-full transition-all",
							"text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]",
							"hover:bg-[var(--color-bg-elevated)]/80"
						)}
						title="Agent settings"
					>
						<Settings class="w-4 h-4 sm:w-[18px] sm:h-[18px]" />
					</button>
				{/if}

				<!-- Send button - perfectly circular -->
				<button
					type="submit"
					disabled={!message.trim() || isLoading || disabled || !$selectedAgent || hasInsufficientBalance}
					class={cn(
						"flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 rounded-full transition-all duration-200",
						"bg-gradient-to-br from-[var(--color-accent-primary)] via-[var(--color-accent-primary)] to-[var(--color-accent-dim)]",
						"text-black",
						"hover:scale-105 hover:shadow-[0_0_20px_rgba(249,115,22,0.5)]",
						"active:scale-95",
						"disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none"
					)}
				>
					{#if isLoading}
						<Loader2 class="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
					{:else}
						<Send class="w-4 h-4 sm:w-5 sm:h-5 translate-x-[1px]" />
					{/if}
				</button>
			</div>
		</div>
	</div>

	<!-- Cost indicator floating above -->
	{#if $selectedAgent && message.trim() && !hasInsufficientBalance}
		<div class="absolute -top-8 left-1/2 -translate-x-1/2 text-[10px] sm:text-xs text-[var(--color-text-muted)] bg-[var(--color-bg-tertiary)]/80 backdrop-blur-sm px-3 py-1 rounded-full border border-[var(--color-border-default)]">
			<span class="text-[var(--color-accent-primary)] font-medium">{promptCost}</span> sats
		</div>
	{/if}
</form>

