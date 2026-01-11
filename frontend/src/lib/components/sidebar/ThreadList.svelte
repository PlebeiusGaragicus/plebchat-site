<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { threads, currentThreadId, type Thread } from '$lib/stores/threads.js';
	import { syncThreadFromServer } from '$lib/stores/stream.svelte.js';
	import { MessageSquare, Trash2, RefreshCw } from '@lucide/svelte';
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

{#if agentThreads.length === 0}
	<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
		No conversations yet.<br />
		Start a new chat!
	</div>
{:else}
	<div class="space-y-1">
		{#each agentThreads as thread (thread.id)}
			<div
				class={cn(
					'w-full group flex items-start gap-2 px-3 py-2 rounded-lg transition-colors text-left',
					'hover:bg-[var(--color-bg-elevated)]',
					$currentThreadId === thread.id && 'bg-[var(--color-bg-elevated)]'
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
					onclick={(e) => requestDelete(e, thread.id)}
					class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-red-error)]/20 text-[var(--color-text-muted)] hover:text-[var(--color-red-error)] transition-all"
					title="Delete thread"
				>
					<Trash2 class="w-3.5 h-3.5" />
				</button>
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
