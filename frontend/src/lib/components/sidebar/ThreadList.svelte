<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { threads, currentThreadId, type Thread } from '$lib/stores/threads.js';
	import { syncThreadFromServer } from '$lib/stores/stream.svelte.js';
	import { MessageSquare, Trash2, Pin, PinOff, ChevronDown, ChevronRight } from '@lucide/svelte';
	import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';

	interface Props {
		threads: Thread[];
		onThreadSelect?: () => void;
	}

	let { threads: agentThreads, onThreadSelect }: Props = $props();

	// Delete confirmation state
	let showDeleteConfirm = $state(false);
	let threadToDelete = $state<string | null>(null);
	let syncingThreadId = $state<string | null>(null);

	// Collapsed state for each group
	let collapsedGroups = $state<Record<string, boolean>>({});

	function toggleGroup(groupKey: string) {
		collapsedGroups[groupKey] = !collapsedGroups[groupKey];
	}

	function isGroupCollapsed(groupKey: string): boolean {
		return collapsedGroups[groupKey] ?? false;
	}

	function togglePin(e: Event, threadId: string) {
		e.stopPropagation();
		threads.togglePin(threadId);
	}

	// Group threads by date category
	type DateGroup = {
		key: string;
		label: string;
		threads: Thread[];
	};

	function getDateGroup(timestamp: number): string {
		const date = new Date(timestamp);
		const now = new Date();
		const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
		const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
		const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
		const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

		if (date >= today) return 'today';
		if (date >= yesterday) return 'yesterday';
		if (date >= lastWeek) return 'week';
		if (date >= lastMonth) return 'month';
		return 'older';
	}

	const groupLabels: Record<string, string> = {
		pinned: 'Pinned',
		today: 'Today',
		yesterday: 'Yesterday',
		week: 'Previous 7 Days',
		month: 'Previous 30 Days',
		older: 'Older'
	};

	// Derive grouped threads
	let groupedThreads = $derived.by(() => {
		const pinned = agentThreads.filter((t) => t.pinned);
		const unpinned = agentThreads.filter((t) => !t.pinned);

		const groups: DateGroup[] = [];

		// Add pinned group if any
		if (pinned.length > 0) {
			groups.push({
				key: 'pinned',
				label: groupLabels.pinned,
				threads: pinned
			});
		}

		// Group unpinned by date
		const dateGroups: Record<string, Thread[]> = {};
		for (const thread of unpinned) {
			const group = getDateGroup(thread.createdAt);
			if (!dateGroups[group]) dateGroups[group] = [];
			dateGroups[group].push(thread);
		}

		// Add date groups in order
		const order = ['today', 'yesterday', 'week', 'month', 'older'];
		for (const key of order) {
			if (dateGroups[key]?.length) {
				groups.push({
					key,
					label: groupLabels[key],
					threads: dateGroups[key]
				});
			}
		}

		return groups;
	});

	async function selectThread(threadId: string) {
		currentThreadId.set(threadId);

		// Sync with server to ensure we have complete message history
		syncingThreadId = threadId;
		try {
			await syncThreadFromServer(threadId);
		} catch (error) {
			console.error('[ThreadList] Failed to sync thread:', error);
		} finally {
			syncingThreadId = null;
		}

		onThreadSelect?.();
	}

	function requestDelete(e: Event, threadId: string) {
		e.stopPropagation();
		threadToDelete = threadId;
		showDeleteConfirm = true;
	}

	function confirmDelete() {
		if (threadToDelete) {
			threads.deleteThread(threadToDelete);
			if ($currentThreadId === threadToDelete) {
				currentThreadId.set(null);
			}
			threadToDelete = null;
		}
	}

	function cancelDelete() {
		threadToDelete = null;
	}

	// Get title of thread being deleted for confirmation message
	let threadToDeleteTitle = $derived(
		threadToDelete ? agentThreads.find((t) => t.id === threadToDelete)?.title || 'this thread' : ''
	);
</script>

{#snippet threadItem(thread: Thread)}
	<div
		class={cn(
			'w-full group flex items-center gap-2 px-3 py-2 rounded-xl transition-all text-left',
			'hover:bg-white/5',
			$currentThreadId === thread.id && 'bg-white/8 border border-white/10'
		)}
	>
		<button
			onclick={() => selectThread(thread.id)}
			class="flex-1 flex items-center gap-2 text-left min-w-0"
		>
			<MessageSquare class="w-4 h-4 flex-shrink-0 text-[var(--color-text-muted)]" />
			<span class="text-xs sm:text-sm text-[var(--color-text-primary)] truncate">
				{thread.title}
			</span>
		</button>
		<div class="flex items-center gap-0.5 flex-shrink-0">
			<button
				onclick={(e) => togglePin(e, thread.id)}
				class={cn(
					'p-1 rounded transition-all',
					thread.pinned
						? 'opacity-100 text-[var(--color-accent-primary)]'
						: 'opacity-0 group-hover:opacity-100 text-[var(--color-text-muted)] hover:text-[var(--color-accent-primary)]',
					'hover:bg-[var(--color-accent-primary)]/10'
				)}
				title={thread.pinned ? 'Unpin thread' : 'Pin thread'}
			>
				{#if thread.pinned}
					<PinOff class="w-3.5 h-3.5" />
				{:else}
					<Pin class="w-3.5 h-3.5" />
				{/if}
			</button>
			<button
				onclick={(e) => requestDelete(e, thread.id)}
				class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-red-error)]/20 text-[var(--color-text-muted)] hover:text-[var(--color-red-error)] transition-all"
				title="Delete thread"
			>
				<Trash2 class="w-3.5 h-3.5" />
			</button>
		</div>
	</div>
{/snippet}

{#if agentThreads.length === 0}
	<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
		No conversations yet.<br />
		Start a new chat!
	</div>
{:else}
	<div class="space-y-2">
		{#each groupedThreads as group (group.key)}
			<div class="space-y-0.5">
				<!-- Group header -->
				<button
					onclick={() => toggleGroup(group.key)}
					class={cn(
						'w-full flex items-center gap-2 px-2 py-1.5 rounded-lg transition-all',
						'hover:bg-white/5 text-left',
						group.key === 'pinned' && 'text-[var(--color-accent-primary)]'
					)}
				>
					{#if isGroupCollapsed(group.key)}
						<ChevronRight class="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
					{:else}
						<ChevronDown class="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
					{/if}
					<span
						class={cn(
							'text-[11px] font-medium uppercase tracking-wider',
							group.key === 'pinned'
								? 'text-[var(--color-accent-primary)]'
								: 'text-[var(--color-text-muted)]'
						)}
					>
						{group.label}
					</span>
					<span class="text-[10px] text-[var(--color-text-muted)]">
						({group.threads.length})
					</span>
				</button>

				<!-- Group content -->
				{#if !isGroupCollapsed(group.key)}
					<div class="pl-1 space-y-0.5">
						{#each group.threads as thread (thread.id)}
							{@render threadItem(thread)}
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<!-- Delete Confirmation Dialog -->
<ConfirmDialog
	bind:open={showDeleteConfirm}
	title="Delete conversation?"
	description="'{threadToDeleteTitle}' will be permanently deleted. This action cannot be undone."
	confirmLabel="Delete"
	cancelLabel="Cancel"
	variant="destructive"
	onConfirm={confirmDelete}
	onCancel={cancelDelete}
/>
