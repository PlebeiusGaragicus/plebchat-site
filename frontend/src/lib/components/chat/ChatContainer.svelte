<script lang="ts">
	import { currentThread, threads, currentThreadId } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { sendMessage, getStreamState, clearRefundToken, TESTING_MODE, TESTING_MODE_COST, type PaymentInfo } from '$lib/stores/stream.svelte.js';
	import { cyphertap } from 'cyphertap';
	import { toast } from 'svelte-sonner';
	import ChatMessage from './ChatMessage.svelte';
	import ChatInput from './ChatInput.svelte';
	import { tick } from 'svelte';

	let messagesContainer: HTMLDivElement;
	let streamState = $derived(getStreamState());
	let isProcessingRefund = $state(false);

	// Auto-scroll to bottom when new messages arrive
	$effect(() => {
		const thread = $currentThread;
		if (thread?.messages.length) {
			tick().then(() => {
				if (messagesContainer) {
					messagesContainer.scrollTop = messagesContainer.scrollHeight;
				}
			});
		}
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
			await cyphertap.redeemEcashToken(refundToken);
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

		// Calculate cost - use TESTING_MODE_COST in testing mode
		const thread = $currentThread;
		const cost = TESTING_MODE 
			? TESTING_MODE_COST 
			: ((!thread || thread.promptCount === 0) 
				? agent.initialCost 
				: agent.additionalCost);

		// Check balance
		if (cyphertap.balance < cost) {
			toast.error('Insufficient balance', {
				description: `You need ${cost} sats but only have ${cyphertap.balance} sats`
			});
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
<div class="flex flex-col h-[calc(100vh-3.5rem)]">
	<!-- Messages area -->
	<div 
		bind:this={messagesContainer}
		class="flex-1 overflow-y-auto"
	>
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
							<span class="text-[var(--color-cyan-glow)]">{$selectedAgent.initialCost}</span> sats to start
							{#if $selectedAgent.additionalCost > 0}
								• <span class="text-[var(--color-cyan-glow)]">+{$selectedAgent.additionalCost}</span> per prompt
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
			<div class="max-w-4xl mx-auto px-2 sm:px-0">
				{#each $currentThread.messages as message, index (message.id)}
					<ChatMessage 
						{message}
						isStreaming={streamState.isLoading && index === $currentThread.messages.length - 1 && message.type === 'ai'}
					/>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Input area -->
	<div class="border-t border-[var(--color-border-default)] bg-[var(--color-bg-primary)]/80 backdrop-blur-sm">
		<div class="max-w-4xl mx-auto p-3 sm:p-4">
			<ChatInput 
				onSubmit={handleSubmit}
				isLoading={streamState.isLoading}
				disabled={!cyphertap.isLoggedIn}
			/>
			
			{#if !cyphertap.isLoggedIn}
				<p class="mt-2 text-[10px] sm:text-xs text-center text-[var(--color-text-muted)]">
					Log in with your wallet to start chatting
				</p>
			{/if}
		</div>
	</div>
</div>
