<script lang="ts">
	import Skeleton from '$lib/components/ui/Skeleton.svelte';
	import { cn } from '$lib/utils.js';

	interface Props {
		type?: 'human' | 'ai';
	}

	let { type = 'ai' }: Props = $props();
</script>

<div
	class={cn(
		'flex gap-2 sm:gap-3 px-3 sm:px-4 py-3 sm:py-4',
		type === 'human' && 'flex-row-reverse bg-transparent',
		type === 'ai' && 'bg-[var(--color-bg-secondary)]/50'
	)}
>
	<!-- Avatar skeleton -->
	<Skeleton
		class={cn(
			'flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-lg',
			type === 'human' && 'bg-[var(--color-purple-dim)]/30',
			type === 'ai' && 'bg-[var(--color-accent-primary)]/20'
		)}
	/>

	<!-- Content skeleton -->
	<div class={cn('flex-1 min-w-0 space-y-2', type === 'human' && 'flex flex-col items-end')}>
		<!-- Name -->
		<Skeleton class="h-4 w-16" />

		<!-- Message bubble -->
		<div
			class={cn(
				'space-y-2 rounded-2xl p-3',
				type === 'human' && 'bg-[var(--color-purple-dim)]/10 rounded-tr-sm max-w-[80%]',
				type === 'ai' && 'bg-[var(--color-bg-elevated)] rounded-tl-sm'
			)}
		>
			<Skeleton class="h-4 w-full" />
			<Skeleton class="h-4 w-[90%]" />
			{#if type === 'ai'}
				<Skeleton class="h-4 w-[75%]" />
				<Skeleton class="h-4 w-[60%]" />
			{/if}
		</div>
	</div>
</div>
