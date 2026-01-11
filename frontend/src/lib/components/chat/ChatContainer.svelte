<script lang="ts">
	import { currentThread, threads, currentThreadId } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import {
		sendMessage,
		getStreamState,
		clearRefundToken,
		syncThreadFromServer,
		type PaymentInfo
	} from '$lib/stores/stream.svelte.js';
	import { cyphertap } from 'cyphertap';
	import { toast } from 'svelte-sonner';
	import { tick, onMount } from 'svelte';
	import ChatMessage from './ChatMessage.svelte';
	import ChatInput from './ChatInput.svelte';
	import SettingsDrawer from './SettingsDrawer.svelte';

	let messagesContainer = $state<HTMLDivElement | null>(null);
	let messagesListContainer = $state<HTMLDivElement | null>(null);
	let streamState = $derived(getStreamState());
	let isProcessingRefund = $state(false);
	let showSettings = $state(false);
	let previousMessageCount = $state(0);
	let lastSyncedThreadId = $state<string | null>(null);
	let isSyncing = $state(false);

	// Sync thread from server when thread changes (ensures complete message history)
	$effect(() => {
		const threadId = $currentThreadId;
		if (threadId && threadId !== lastSyncedThreadId && !streamState.isLoading) {
			syncCurrentThread(threadId);
		}
	});

	async function syncCurrentThread(threadId: string) {
		if (isSyncing) return;
		isSyncing = true;
		lastSyncedThreadId = threadId;
		
		try {
			const success = await syncThreadFromServer(threadId);
			if (success) {
				console.log('[ChatContainer] Thread synced from server');
			}
		} catch (error) {
			console.error('[ChatContainer] Failed to sync thread:', error);
		} finally {
			isSyncing = false;
		}
	}

	// Scroll to position the last human message at the TOP of the viewport
	async function scrollHumanMessageToTop() {
		await tick(); // Wait for DOM to update
		
		// Small additional delay to ensure rendering is complete
		await new Promise(resolve => setTimeout(resolve, 50));
		
		if (!messagesContainer || !messagesListContainer) return;

		// Find the last message element (should be the human message we just added)
		const messageElements = messagesListContainer.querySelectorAll('[data-message]');
		const lastMessageEl = messageElements[messageElements.length - 1] as HTMLElement;

		if (lastMessageEl) {
			// Use scrollIntoView to bring the message to the top
			lastMessageEl.scrollIntoView({
				behavior: 'smooth',
				block: 'start'
			});
		}
	}

	// Only scroll when a NEW human message is added (not during AI streaming)
	$effect(() => {
		const thread = $currentThread;
		if (!thread || !messagesContainer) return;

		const currentCount = thread.messages.length;
		const lastMessage = thread.messages[currentCount - 1];

		// Only auto-scroll when a new human message is added
		if (currentCount > previousMessageCount && lastMessage?.type === 'human') {
			scrollHumanMessageToTop();
		}

		previousMessageCount = currentCount;
	});

	// Handle errors and auto-redeem refund tokens
	$effect(() => {
		const state = streamState;

		// Show error toast if there's an error
		if (state.error && !state.isLoading) {
			toast.error('Request failed', {
				description: state.error
			});
		}

		// Auto-redeem refund token if available
		if (state.refundToken && !state.isLoading && !isProcessingRefund) {
			processRefund(state.refundToken);
		}
	});

	async function processRefund(refundToken: string) {
		isProcessingRefund = true;
		try {
			console.log('[Refund] Auto-redeeming refund token...');
			await cyphertap.receiveEcashToken(refundToken);
			toast.success('Payment refunded', {
				description: 'Your ecash has been returned to your wallet'
			});
		} catch (error) {
			console.error('[Refund] Failed to auto-redeem:', error);
			// Show the token so user can manually redeem
			toast.error('Could not auto-refund payment', {
				description: 'Please copy this token to recover your funds',
				duration: 10000
			});
			// Log the token for manual recovery
			console.log('[Refund] Manual recovery token:', refundToken);
		} finally {
			clearRefundToken();
			isProcessingRefund = false;
		}
	}

	async function handleSubmit(message: string) {
		const agent = $selectedAgent;
		if (!agent) {
			toast.error('Please select an agent first');
			return;
		}

		// Check if user is logged in
		if (!cyphertap.isLoggedIn) {
			toast.error('Please log in to use the chat', {
				description: 'Click the wallet button in the top right to get started'
			});
			return;
		}

		const thread = $currentThread;
		const cost = !thread || thread.promptCount === 0 ? agent.initialCost : agent.additionalCost;

		// Check balance (this is a safety check - the UI should prevent submission when balance is low)
		if (cyphertap.balance < cost) {
			return;
		}

		// Generate ecash token for payment
		let payment: PaymentInfo | undefined;
		try {
			const tokenResult = await cyphertap.generateEcashToken(cost, `PlebChat prompt`);
			payment = {
				ecash_token: tokenResult.token,
				amount_sats: cost,
				mint: tokenResult.mint
			};
		} catch (error) {
			toast.error('Failed to generate payment token', {
				description: error instanceof Error ? error.message : 'Unknown error'
			});
			return;
		}

		// If no current thread, create one
		if (!$currentThreadId) {
			const newThread = threads.createThread(agent.id, message);
			currentThreadId.set(newThread.id);
		}

		// Send message with payment
		await sendMessage({
			message,
			payment,
			threadId: $currentThreadId || undefined
		});
	}
</script>

<!-- Main content area - sidebar overlays this, doesn't push it -->
<div class="relative h-[calc(100vh-3.5rem)] h-[calc(100dvh-3.5rem)]">
	<!-- Messages area -->
	<div bind:this={messagesContainer} class="h-full overflow-y-auto overscroll-contain pb-28 sm:pb-32">
		{#if !$currentThread || $currentThread.messages.length === 0}
			<!-- Empty state -->
			<div class="h-full flex items-center justify-center px-4">
				<div class="text-center max-w-md">
					{#if $selectedAgent}
						<div class="text-4xl sm:text-5xl mb-3 sm:mb-4">{$selectedAgent.emoji}</div>
						<h2 class="text-lg sm:text-xl font-semibold text-[var(--color-text-primary)] mb-2">
							{$selectedAgent.name}
						</h2>
						<p class="text-sm sm:text-base text-[var(--color-text-secondary)] mb-4">
							{$selectedAgent.description}
						</p>
						<div class="text-xs sm:text-sm text-[var(--color-text-muted)]">
							<span class="text-[var(--color-accent-primary)]">{$selectedAgent.initialCost}</span> sats
							to start
							{#if $selectedAgent.additionalCost > 0}
								• <span class="text-[var(--color-accent-primary)]"
									>+{$selectedAgent.additionalCost}</span
								>
								per prompt
							{/if}
						</div>
					{:else}
						<div class="text-4xl sm:text-5xl mb-3 sm:mb-4">🤖</div>
						<h2 class="text-lg sm:text-xl font-semibold text-[var(--color-text-primary)] mb-2">
							Select an Agent
						</h2>
						<p class="text-sm sm:text-base text-[var(--color-text-secondary)]">
							Choose an AI agent from the dropdown above to start chatting
						</p>
					{/if}
				</div>
			</div>
		{:else}
			<!-- Messages list -->
			<div bind:this={messagesListContainer} class="max-w-4xl mx-auto px-2 sm:px-0">
				{#each $currentThread.messages as message, index (message.id)}
					<div data-message={message.id}>
						<ChatMessage
							{message}
							isStreaming={streamState.isLoading &&
								index === $currentThread.messages.length - 1 &&
								message.type === 'ai'}
						/>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Floating input area -->
	<div class="absolute bottom-4 sm:bottom-6 left-4 right-4 sm:left-8 sm:right-8 z-20">
		<div class="max-w-3xl mx-auto">
			<ChatInput
				onSubmit={handleSubmit}
				isLoading={streamState.isLoading}
				disabled={!cyphertap.isLoggedIn}
				balance={cyphertap.balance}
				onOpenSettings={() => (showSettings = true)}
			/>

			{#if !cyphertap.isLoggedIn}
				<p class="mt-3 text-[10px] sm:text-xs text-center text-[var(--color-text-muted)]">
					Log in with your wallet to start chatting
				</p>
			{/if}
		</div>
	</div>
</div>

<!-- Settings Drawer -->
<SettingsDrawer bind:open={showSettings} agent={$selectedAgent} />
