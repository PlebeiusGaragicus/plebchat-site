<script lang="ts">
	import { AGENTS, selectedAgent, type Agent } from '$lib/stores/agent.js';
	import { Zap, Shield, Coins, Globe, Lock, ArrowRight, Check } from '@lucide/svelte';
	import { cyphertap } from 'cyphertap';
	import { goto } from '$app/navigation';
	import { cn } from '$lib/utils.js';

	function selectAgent(agent: Agent) {
		if (agent.available) {
			selectedAgent.select(agent);
			// Scroll to top for chat experience
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}
</script>

<div class="min-h-[calc(100vh-3.5rem)] flex flex-col">
	<!-- Hero Section -->
	<section class="flex-1 flex items-center justify-center px-4 py-8 sm:py-16">
		<div class="max-w-3xl mx-auto text-center">
			<div class="mb-4 sm:mb-6 inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
				<Zap class="w-3 h-3 sm:w-4 sm:h-4 text-[var(--color-cyan-glow)]" />
				<span class="text-xs sm:text-sm text-[var(--color-text-secondary)]">Powered by Bitcoin</span>
			</div>

			<h1 class="text-3xl sm:text-5xl lg:text-6xl font-bold text-[var(--color-text-primary)] mb-4 sm:mb-6 leading-tight">
				AI Chat, 
				<span class="text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-cyan-glow)] to-[var(--color-purple-accent)]">
					Pay-Per-Use
				</span>
			</h1>

			<p class="text-base sm:text-xl text-[var(--color-text-secondary)] mb-6 sm:mb-8 max-w-2xl mx-auto px-2">
				Chat with AI agents using Bitcoin micropayments. No subscriptions, no accounts, no data collection. 
				Just pay for what you use with ecash.
			</p>

			<div class="flex flex-col sm:flex-row gap-4 justify-center">
				{#if cyphertap.isLoggedIn}
					<a 
						href="#agents"
						class="btn btn-primary px-6 py-3 text-base sm:text-lg"
					>
						<span>Start Chatting</span>
						<ArrowRight class="w-5 h-5" />
					</a>
				{:else}
					<div class="text-[var(--color-text-secondary)]">
						<p class="mb-2 text-sm sm:text-base">Click the wallet button above to get started</p>
						<p class="text-xs sm:text-sm text-[var(--color-text-muted)]">No signup required • Just a key pair</p>
					</div>
				{/if}
			</div>
		</div>
	</section>

	<!-- Features Grid -->
	<section class="px-4 py-8 sm:py-16 bg-[var(--color-bg-secondary)]/30">
		<div class="max-w-5xl mx-auto">
			<h2 class="text-xl sm:text-2xl font-bold text-center text-[var(--color-text-primary)] mb-8 sm:mb-12">
				Why PlebChat?
			</h2>

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
				<!-- Feature 1 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gradient-to-br from-[var(--color-cyan-glow)] to-[var(--color-cyan-dim)] flex items-center justify-center mb-3 sm:mb-4">
						<Coins class="w-5 h-5 sm:w-6 sm:h-6 text-[var(--color-bg-primary)]" />
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">Pay Per Use</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						No monthly subscriptions. Pay only for what you use with Bitcoin micropayments.
					</p>
				</div>

				<!-- Feature 2 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gradient-to-br from-[var(--color-purple-accent)] to-[var(--color-purple-dim)] flex items-center justify-center mb-3 sm:mb-4">
						<Shield class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">Self Custody</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						Your keys, your coins. Ecash tokens stay on your device until you spend them.
					</p>
				</div>

				<!-- Feature 3 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gradient-to-br from-[var(--color-green-success)] to-emerald-600 flex items-center justify-center mb-3 sm:mb-4">
						<Lock class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">No Accounts</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						No email, no password, no KYC. Just a cryptographic key pair using Nostr.
					</p>
				</div>

				<!-- Feature 4 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gradient-to-br from-[var(--color-amber-warning)] to-orange-500 flex items-center justify-center mb-3 sm:mb-4">
						<Globe class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">Permissionless</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						Anyone in the world can use this service. No restrictions or censorship.
					</p>
				</div>

				<!-- Feature 5 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] flex items-center justify-center mb-3 sm:mb-4">
						<span class="text-xl sm:text-2xl">💾</span>
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">Local Storage</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						All your data stays in your browser. We don't store your conversations.
					</p>
				</div>

				<!-- Feature 6 -->
				<div class="p-4 sm:p-6 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
					<div class="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] flex items-center justify-center mb-3 sm:mb-4">
						<span class="text-xl sm:text-2xl">⚡</span>
					</div>
					<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)] mb-2">Instant Payments</h3>
					<p class="text-[var(--color-text-secondary)] text-xs sm:text-sm">
						Ecash tokens are validated instantly. No waiting for confirmations.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Agents Section -->
	<section id="agents" class="px-4 py-8 sm:py-16">
		<div class="max-w-5xl mx-auto">
			<h2 class="text-xl sm:text-2xl font-bold text-center text-[var(--color-text-primary)] mb-3 sm:mb-4">
				Available Agents
			</h2>
			<p class="text-center text-[var(--color-text-secondary)] text-sm sm:text-base mb-8 sm:mb-12 max-w-xl mx-auto">
				Choose an AI agent that fits your needs. More agents coming soon!
			</p>

			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
				{#each AGENTS as agent}
					<button
						onclick={() => selectAgent(agent)}
						disabled={!agent.available}
						class={cn(
							"p-4 sm:p-6 rounded-xl text-left transition-all duration-200",
							"bg-[var(--color-bg-secondary)] border-2",
							agent.available && "cursor-pointer hover:border-[var(--color-cyan-glow)] hover:shadow-[var(--shadow-glow-sm)]",
							agent.available && $selectedAgent?.id === agent.id && "border-[var(--color-cyan-glow)] shadow-[var(--shadow-glow-sm)]",
							agent.available && $selectedAgent?.id !== agent.id && "border-[var(--color-border-default)]",
							!agent.available && "opacity-60 cursor-not-allowed border-[var(--color-border-default)]"
						)}
					>
						<div class="flex items-start gap-3 mb-3 sm:mb-4">
							<span class="text-2xl sm:text-3xl">{agent.emoji}</span>
							<div class="flex-1">
								<div class="flex items-center gap-2">
									<h3 class="text-base sm:text-lg font-semibold text-[var(--color-text-primary)]">{agent.name}</h3>
									{#if $selectedAgent?.id === agent.id}
										<Check class="w-4 h-4 text-[var(--color-cyan-glow)]" />
									{/if}
								</div>
								{#if !agent.available}
									<span class="text-[10px] sm:text-xs text-[var(--color-text-muted)] bg-[var(--color-bg-elevated)] px-2 py-0.5 rounded">Coming Soon</span>
								{/if}
							</div>
						</div>
						<p class="text-xs sm:text-sm text-[var(--color-text-secondary)] mb-3 sm:mb-4">
							{agent.description}
						</p>
						<div class="flex items-center justify-between text-xs sm:text-sm">
							<span class="text-[var(--color-text-muted)]">
								<span class="text-[var(--color-cyan-glow)]">{agent.initialCost}</span> sats
								{#if agent.additionalCost > 0}
									• +{agent.additionalCost}/prompt
								{/if}
							</span>
							{#if agent.fileUpload !== 'none'}
								<span class="text-[10px] sm:text-xs text-[var(--color-text-muted)] bg-[var(--color-bg-elevated)] px-2 py-0.5 rounded">
									📎 {agent.fileUpload}
								</span>
							{/if}
						</div>
					</button>
				{/each}
			</div>
		</div>
	</section>

	<!-- Footer -->
	<footer class="px-4 py-6 sm:py-8 border-t border-[var(--color-border-default)]">
		<div class="max-w-5xl mx-auto text-center text-xs sm:text-sm text-[var(--color-text-muted)]">
			<p>Give me freedom, or give me death.</p>
		</div>
	</footer>
</div>
