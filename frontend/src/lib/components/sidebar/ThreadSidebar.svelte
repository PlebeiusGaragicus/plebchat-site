<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { threads, currentThreadId, getThreadsForAgent } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { PanelLeftClose, PanelLeft, Plus, MessageSquare, Trash2, X } from '@lucide/svelte';
	import { get } from 'svelte/store';

	interface Props {
		isOpen: boolean;
		onToggle: () => void;
	}

	let { isOpen, onToggle }: Props = $props();

	// Get threads for the selected agent
	let agentThreads = $derived.by(() => {
		const agent = $selectedAgent;
		if (!agent) return [];
		const threadStore = getThreadsForAgent(agent.id);
		return get(threadStore);
	});

	function formatDate(timestamp: number): string {
		const date = new Date(timestamp);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));
		
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days}d ago`;
		return date.toLocaleDateString();
	}

	function selectThread(threadId: string) {
		currentThreadId.set(threadId);
		// Close sidebar on mobile after selection
		if (window.innerWidth < 768) {
			onToggle();
		}
	}

	function startNewChat() {
		currentThreadId.set(null);
		// Close sidebar on mobile
		if (window.innerWidth < 768) {
			onToggle();
		}
	}

	function deleteThread(e: Event, threadId: string) {
		e.stopPropagation();
		threads.deleteThread(threadId);
		if ($currentThreadId === threadId) {
			currentThreadId.set(null);
		}
	}
</script>

<!-- Mobile overlay backdrop -->
{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div 
		class="md:hidden fixed inset-0 bg-black/50 z-30 transition-opacity"
		onclick={onToggle}
	></div>
{/if}

<!-- Toggle button (desktop only) -->
<button
	onclick={onToggle}
	class={cn(
		"hidden md:flex fixed left-4 top-20 z-40 p-2 rounded-lg transition-all",
		"bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]",
		"hover:bg-[var(--color-bg-elevated)] hover:border-[var(--color-border-hover)]",
		"text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]",
		isOpen && "left-[276px]"
	)}
	title={isOpen ? "Close sidebar" : "Open sidebar"}
>
	{#if isOpen}
		<PanelLeftClose class="w-5 h-5" />
	{:else}
		<PanelLeft class="w-5 h-5" />
	{/if}
</button>

<!-- Mobile toggle button (in navbar area) -->
<button
	onclick={onToggle}
	class={cn(
		"md:hidden fixed left-4 top-[4.5rem] z-40 p-2 rounded-lg transition-all",
		"bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]",
		"hover:bg-[var(--color-bg-elevated)]",
		"text-[var(--color-text-muted)]"
	)}
	title={isOpen ? "Close sidebar" : "Open sidebar"}
>
	{#if isOpen}
		<X class="w-5 h-5" />
	{:else}
		<PanelLeft class="w-5 h-5" />
	{/if}
</button>

<!-- Sidebar panel -->
<aside class={cn(
	"fixed left-0 top-14 bottom-0 z-40 md:z-30",
	"w-[85vw] max-w-[300px] md:w-72",
	"bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-default)]",
	"transition-transform duration-300 ease-in-out",
	isOpen ? "translate-x-0" : "-translate-x-full"
)}>
	<div class="flex flex-col h-full">
		<!-- Header -->
		<div class="p-3 sm:p-4 border-b border-[var(--color-border-default)]">
			<button
				onclick={startNewChat}
				class={cn(
					"w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors",
					"border border-[var(--color-border-default)]",
					"hover:bg-[var(--color-bg-elevated)] hover:border-[var(--color-border-hover)]",
					"text-[var(--color-text-primary)]"
				)}
			>
				<Plus class="w-4 h-4" />
				<span class="text-sm font-medium">New Chat</span>
			</button>
		</div>

		<!-- Thread list -->
		<div class="flex-1 overflow-y-auto p-2">
			{#if !$selectedAgent}
				<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
					Select an agent to view chat history
				</div>
			{:else if agentThreads.length === 0}
				<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
					No conversations yet.<br/>
					Start a new chat!
				</div>
			{:else}
				<div class="space-y-1">
					{#each agentThreads as thread (thread.id)}
						<div
							class={cn(
								"w-full group flex items-start gap-2 px-3 py-2 rounded-lg transition-colors text-left",
								"hover:bg-[var(--color-bg-elevated)]",
								$currentThreadId === thread.id && "bg-[var(--color-bg-elevated)]"
							)}
						>
							<button
								onclick={() => selectThread(thread.id)}
								class="flex-1 flex items-start gap-2 text-left min-w-0"
							>
								<MessageSquare class="w-4 h-4 mt-0.5 flex-shrink-0 text-[var(--color-text-muted)]" />
								<div class="flex-1 min-w-0">
									<div class="text-xs sm:text-sm text-[var(--color-text-primary)] truncate">
										{thread.title}
									</div>
									<div class="text-[10px] sm:text-xs text-[var(--color-text-muted)]">
										{formatDate(thread.updatedAt)}
									</div>
								</div>
							</button>
							<button
								onclick={(e) => deleteThread(e, thread.id)}
								class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-red-error)]/20 text-[var(--color-text-muted)] hover:text-[var(--color-red-error)] transition-all"
								title="Delete thread"
							>
								<Trash2 class="w-3.5 h-3.5" />
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Footer -->
		<div class="p-3 sm:p-4 border-t border-[var(--color-border-default)]">
			<div class="text-[10px] sm:text-xs text-[var(--color-text-muted)] text-center">
				Stored locally in your browser
			</div>
		</div>
	</div>
</aside>
