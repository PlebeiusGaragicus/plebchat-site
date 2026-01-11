<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { threads, currentThreadId, filterThreadsByAgent } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { sidebar } from '$lib/stores/sidebar.svelte.js';
	import { PanelLeftClose, PanelLeft, Plus } from '@lucide/svelte';
	import { Drawer } from 'vaul-svelte';
	import ThreadList from './ThreadList.svelte';

	// Reactively filter threads for the selected agent using Svelte 5 runes
	let agentThreads = $derived(filterThreadsByAgent($threads, $selectedAgent?.id ?? null));

	function startNewChat() {
		currentThreadId.set(null);
		sidebar.closeMobile();
	}

	function handleThreadSelect() {
		sidebar.closeMobile();
	}

	// Sidebar content (shared between mobile drawer and desktop panel)
</script>

{#snippet sidebarContent()}
	<div class="flex flex-col h-full">
		<!-- Header -->
		<div class="p-3 sm:p-4 border-b border-[var(--color-border-hover)]">
			<button
				onclick={startNewChat}
				class={cn(
					'w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
					'border border-[var(--color-border-hover)]',
					'hover:bg-[var(--color-bg-elevated)] hover:border-[var(--color-border-bright)]',
					'text-[var(--color-text-primary)]'
				)}
			>
				<Plus class="w-4 h-4" />
				<span class="text-sm font-medium">New Chat</span>
			</button>
		</div>

		<!-- Thread list -->
		<div class="flex-1 overflow-y-auto overscroll-contain p-2">
			{#if !$selectedAgent}
				<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
					Select an agent to view chat history
				</div>
			{:else}
				<ThreadList threads={agentThreads} onThreadSelect={handleThreadSelect} />
			{/if}
		</div>

		<!-- Footer -->
		<div class="p-3 sm:p-4 border-t border-[var(--color-border-hover)]">
			<div class="text-[10px] sm:text-xs text-[var(--color-text-muted)] text-center">
				Stored locally in your browser
			</div>
		</div>
	</div>
{/snippet}

<!-- Mobile: Drawer from vaul-svelte -->
{#if sidebar.isMobile}
	<Drawer.Root
		direction="left"
		open={sidebar.mobileOpen}
		onOpenChange={(open) => (sidebar.mobileOpen = open)}
	>
		<Drawer.Portal>
			<Drawer.Overlay class="fixed inset-0 bg-black/50 z-40" />
			<Drawer.Content
				class="fixed left-0 top-0 bottom-0 z-50 w-[85vw] max-w-[300px] bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-hover)] outline-none"
			>
				<Drawer.Title class="sr-only">Chat History</Drawer.Title>
				<Drawer.Description class="sr-only">Your conversation threads</Drawer.Description>
				{@render sidebarContent()}
			</Drawer.Content>
		</Drawer.Portal>
	</Drawer.Root>

	<!-- Mobile toggle button -->
	<button
		onclick={() => sidebar.toggle()}
		class={cn(
			'md:hidden fixed left-4 top-[4.5rem] z-30 p-2 rounded-lg transition-all',
			'bg-[var(--color-bg-secondary)] border border-[var(--color-border-hover)]',
			'hover:bg-[var(--color-bg-elevated)] hover:border-[var(--color-border-bright)]',
			'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
		)}
		title="Open sidebar"
	>
		<PanelLeft class="w-5 h-5" />
	</button>
{:else}
	<!-- Desktop: Fixed sidebar panel -->
	<aside
		class={cn(
			'hidden md:flex fixed left-0 top-14 bottom-0 z-30',
			'w-72 flex-col',
			'bg-[var(--color-bg-secondary)] border-r border-[var(--color-border-hover)]',
			'transition-transform duration-200 ease-in-out',
			sidebar.desktopOpen ? 'translate-x-0' : '-translate-x-full'
		)}
	>
		{@render sidebarContent()}
	</aside>

	<!-- Desktop toggle button -->
	<button
		onclick={() => sidebar.toggle()}
		class={cn(
			'hidden md:flex fixed top-20 z-40 p-2 rounded-lg transition-all',
			'bg-[var(--color-bg-secondary)] border border-[var(--color-border-hover)]',
			'hover:bg-[var(--color-bg-elevated)] hover:border-[var(--color-border-bright)]',
			'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]',
			sidebar.desktopOpen ? 'left-[276px]' : 'left-4'
		)}
		title={sidebar.desktopOpen ? 'Close sidebar (⌘B)' : 'Open sidebar (⌘B)'}
	>
		{#if sidebar.desktopOpen}
			<PanelLeftClose class="w-5 h-5" />
		{:else}
			<PanelLeft class="w-5 h-5" />
		{/if}
	</button>
{/if}
