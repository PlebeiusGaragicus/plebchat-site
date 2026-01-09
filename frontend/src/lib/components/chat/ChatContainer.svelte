<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { currentThread, threads, currentThreadId } from '$lib/stores/threads.js';
	import { selectedAgent } from '$lib/stores/agent.js';
	import { sendMessage, getStreamState, type PaymentInfo } from '$lib/stores/stream.svelte.js';
	import { cyphertap } from 'cyphertap';
	import { toast } from 'svelte-sonner';
	import ChatMessage from './ChatMessage.svelte';
	import ChatInput from './ChatInput.svelte';
	import { onMount, tick } from 'svelte';

	interface Props {
		sidebarOpen: boolean;
	}

	let { sidebarOpen }: Props = $props();

	let messagesContainer: HTMLDivElement;
	let streamState = $derived(getStreamState());

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

		// Calculate cost
		const thread = $currentThread;
		const cost = (!thread || thread.promptCount === 0) 
			? agent.initialCost 
			: agent.additionalCost;

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

<div class={cn(
	"flex flex-col h-[calc(100vh-3.5rem)] transition-all duration-300",
	sidebarOpen && "ml-72"
)}>
	<!-- Messages area -->
	<div 
		bind:this={messagesContainer}
		class="flex-1 overflow-y-auto"
	>
		{#if !$currentThread || $currentThread.messages.length === 0}
			<!-- Empty state -->
			<div class="h-full flex items-center justify-center">
				<div class="text-center px-4 max-w-md">
					{#if $selectedAgent}
						<div class="text-4xl mb-4">{$selectedAgent.emoji}</div>
						<h2 class="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
							{$selectedAgent.name}
						</h2>
						<p class="text-[var(--color-text-secondary)] mb-4">
							{$selectedAgent.description}
						</p>
						<div class="text-sm text-[var(--color-text-muted)]">
							<span class="text-[var(--color-cyan-glow)]">{$selectedAgent.initialCost}</span> sats to start
							{#if $selectedAgent.additionalCost > 0}
								• <span class="text-[var(--color-cyan-glow)]">+{$selectedAgent.additionalCost}</span> per prompt
							{/if}
						</div>
					{:else}
						<div class="text-4xl mb-4">🤖</div>
						<h2 class="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
							Select an Agent
						</h2>
						<p class="text-[var(--color-text-secondary)]">
							Choose an AI agent from the dropdown above to start chatting
						</p>
					{/if}
				</div>
			</div>
		{:else}
			<!-- Messages list -->
			<div class="max-w-4xl mx-auto">
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
		<div class="max-w-4xl mx-auto p-4">
			<ChatInput 
				onSubmit={handleSubmit}
				isLoading={streamState.isLoading}
				disabled={!cyphertap.isLoggedIn}
			/>
			
			{#if !cyphertap.isLoggedIn}
				<p class="mt-2 text-xs text-center text-[var(--color-text-muted)]">
					Log in with your wallet to start chatting
				</p>
			{/if}
		</div>
	</div>
</div>
