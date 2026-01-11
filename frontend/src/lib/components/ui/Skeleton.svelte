<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		class?: string;
	}

	let { class: className, ...restProps }: Props = $props();
</script>

<div
	class={cn('animate-pulse rounded-md bg-[var(--color-bg-elevated)]', className)}
	{...restProps}
></div>
