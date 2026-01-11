<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { threads, currentThreadId, filterThreadsByAgent, searchThreads } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { sidebar } from '$lib/stores/sidebar.svelte.js';
	import { PanelLeftClose, PanelLeft, Plus, Search, X } from '@lucide/svelte';
	import { Drawer } from 'vaul-svelte';
	import ThreadList from './ThreadList.svelte';

	// Search state
	let searchQuery = $state('');

	// Reactively filter threads for the selected agent using Svelte 5 runes
	let agentThreads = $derived.by(() => {
		const filtered = filterThreadsByAgent($threads, $selectedAgent?.id ?? null);
		return searchThreads(filtered, searchQuery);
	});

	function startNewChat() {
		currentThreadId.set(null);
		sidebar.closeMobile();
	}

	function handleThreadSelect() {
		sidebar.closeMobile();
	}

	function clearSearch() {
		searchQuery = '';
	}

	// Sidebar content (shared between mobile drawer and desktop panel)
</script>

{#snippet sidebarContent()}
	<div class="flex flex-col h-full">
		<!-- Header -->
		<div class="p-3 sm:p-4 border-b border-white/5 space-y-3">
			<button
				onclick={startNewChat}
				class={cn(
					'w-full flex items-center gap-2 px-3 py-2 rounded-xl transition-all',
					'bg-white/5 border border-white/10',
					'hover:bg-white/10 hover:border-white/20',
					'text-[var(--color-text-primary)]',
					'backdrop-blur-sm'
				)}
			>
				<Plus class="w-4 h-4" />
				<span class="text-sm font-medium">New Chat</span>
			</button>

			<!-- Search input -->
			{#if $selectedAgent}
				<div class="relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
					<input
						type="text"
						placeholder="Search conversations..."
						bind:value={searchQuery}
						class={cn(
							'w-full pl-9 pr-8 py-2 text-sm rounded-xl',
							'bg-white/5 border border-white/10',
							'placeholder:text-[var(--color-text-muted)]',
							'text-[var(--color-text-primary)]',
							'focus:outline-none focus:border-white/20 focus:bg-white/10',
							'transition-all backdrop-blur-sm'
						)}
					/>
					{#if searchQuery}
						<button
							onclick={clearSearch}
							class="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
						>
							<X class="w-3.5 h-3.5" />
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Thread list -->
		<div class="flex-1 overflow-y-auto overscroll-contain p-2">
			{#if !$selectedAgent}
				<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
					Select an agent to view chat history
				</div>
			{:else if searchQuery && agentThreads.length === 0}
				<div class="px-3 py-8 text-center text-[var(--color-text-muted)] text-xs sm:text-sm">
					No results for "{searchQuery}"
				</div>
			{:else}
				<ThreadList threads={agentThreads} onThreadSelect={handleThreadSelect} />
			{/if}
		</div>

		<!-- Footer -->
		<div class="p-3 sm:p-4 border-t border-white/5">
			<div class="text-[10px] sm:text-xs text-[var(--color-text-muted)] text-center">
				Stored locally in your browser
			</div>
		</div>
	</div>
{/snippet}

<!-- Mobile: Drawer from vaul-svelte (always rendered, CSS controls visibility) -->
<div class="md:hidden">
	<Drawer.Root
		direction="left"
		open={sidebar.mobileOpen}
		onOpenChange={(open) => (sidebar.mobileOpen = open)}
	>
		<Drawer.Portal>
			<Drawer.Overlay class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
			<Drawer.Content
				class={cn(
					'fixed left-0 top-0 bottom-0 z-50 w-[85vw] max-w-[300px] outline-none',
					'glass-panel border-r border-white/10'
				)}
			>
				<Drawer.Title class="sr-only">Chat History</Drawer.Title>
				<Drawer.Description class="sr-only">Your conversation threads</Drawer.Description>
				{@render sidebarContent()}
			</Drawer.Content>
		</Drawer.Portal>
	</Drawer.Root>

	<!-- Mobile toggle button -->
	<button
		onclick={() => sidebar.open()}
		class={cn(
			'fixed left-4 top-[4.5rem] z-30 p-2 rounded-xl transition-all',
			'glass-panel border border-white/10',
			'hover:bg-white/10 hover:border-white/20',
			'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
		)}
		title="Open sidebar"
	>
		<PanelLeft class="w-5 h-5" />
	</button>
</div>

<!-- Desktop: Fixed sidebar panel (always rendered, CSS controls visibility) -->
<aside
	class={cn(
		'hidden md:flex fixed left-0 top-14 bottom-0 z-30',
		'w-72 flex-col',
		'glass-panel border-r border-white/10',
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
		'hidden md:flex fixed top-20 z-40 p-2 rounded-xl transition-all',
		'glass-panel border border-white/10',
		'hover:bg-white/10 hover:border-white/20',
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
