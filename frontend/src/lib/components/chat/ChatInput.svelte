<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { Send, Settings, Loader2 } from '@lucide/svelte';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { currentThread } from '$lib/stores/threads.js';

	interface Props {
		onSubmit: (message: string) => void;
		isLoading?: boolean;
		disabled?: boolean;
	}

	let { onSubmit, isLoading = false, disabled = false }: Props = $props();
	
	let message = $state('');
	let textareaRef = $state<HTMLTextAreaElement | null>(null);
	let showSettings = $state(false);

	function handleSubmit(e?: Event) {
		e?.preventDefault();
		if (!message.trim() || isLoading || disabled) return;
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
		textareaRef.style.height = Math.min(textareaRef.scrollHeight, 200) + 'px';
	}

	// Calculate cost for current prompt
	let promptCost = $derived.by(() => {
		if (!$selectedAgent) return 0;
		const thread = $currentThread;
		if (!thread || thread.promptCount === 0) {
			return $selectedAgent.initialCost;
		}
		return $selectedAgent.additionalCost;
	});
</script>

<form onsubmit={handleSubmit} class="relative">
	<div class="glow-input p-1">
		<div class="flex items-end gap-2">
			<textarea
				bind:this={textareaRef}
				bind:value={message}
				onkeydown={handleKeyDown}
				oninput={autoResize}
				placeholder={$selectedAgent ? "Ask me anything..." : "Select an agent to start chatting"}
				disabled={disabled || !$selectedAgent}
				rows={1}
				class={cn(
					"flex-1 resize-none bg-transparent px-4 py-3 text-[var(--color-text-primary)]",
					"placeholder:text-[var(--color-text-muted)]",
					"focus:outline-none focus:ring-0",
					"disabled:opacity-50 disabled:cursor-not-allowed",
					"max-h-[200px] min-h-[48px]"
				)}
			></textarea>

			<div class="flex items-center gap-1 pb-2 pr-2">
				<!-- Settings button -->
				<button
					type="button"
					onclick={() => showSettings = !showSettings}
					class={cn(
						"p-2 rounded-lg transition-colors",
						"text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]",
						"hover:bg-[var(--color-bg-elevated)]"
					)}
					title="Agent settings"
				>
					<Settings class="w-5 h-5" />
				</button>

				<!-- Send button -->
				<button
					type="submit"
					disabled={!message.trim() || isLoading || disabled || !$selectedAgent}
					class={cn(
						"p-2 rounded-lg transition-all",
						"bg-gradient-to-r from-[var(--color-cyan-glow)] to-[var(--color-cyan-dim)]",
						"text-[var(--color-bg-primary)] font-medium",
						"hover:shadow-[var(--shadow-glow-sm)]",
						"disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
					)}
				>
					{#if isLoading}
						<Loader2 class="w-5 h-5 animate-spin" />
					{:else}
						<Send class="w-5 h-5" />
					{/if}
				</button>
			</div>
		</div>
	</div>

	<!-- Cost indicator -->
	{#if $selectedAgent && message.trim()}
		<div class="absolute -top-8 right-0 text-xs text-[var(--color-text-muted)]">
			<span class="text-[var(--color-cyan-glow)]">{promptCost}</span> sats
		</div>
	{/if}
</form>

<!-- Settings Modal (placeholder for now) -->
{#if showSettings}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div 
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" 
		onclick={() => showSettings = false}
		role="dialog"
		aria-modal="true"
		aria-labelledby="settings-title"
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)] rounded-xl p-6 max-w-md w-full mx-4" onclick={(e) => e.stopPropagation()}>
			<h3 id="settings-title" class="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Agent Settings</h3>
			<p class="text-[var(--color-text-secondary)] text-sm mb-4">
				Configure {$selectedAgent?.name} settings for this chat session.
			</p>
			<div class="text-[var(--color-text-muted)] text-sm">
				<em>Settings coming soon...</em>
			</div>
			<div class="mt-6 flex justify-end gap-2">
				<button 
					onclick={() => showSettings = false}
					class="btn btn-ghost"
				>
					Close
				</button>
			</div>
		</div>
	</div>
{/if}
