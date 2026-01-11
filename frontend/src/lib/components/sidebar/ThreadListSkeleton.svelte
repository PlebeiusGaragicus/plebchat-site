<script lang="ts">
	import Skeleton from '$lib/components/ui/Skeleton.svelte';

	interface Props {
		count?: number;
	}

	let { count = 5 }: Props = $props();
</script>

<div class="space-y-1">
	{#each Array(count) as _, i}
		<div class="flex items-start gap-2 px-3 py-2">
			<Skeleton class="w-4 h-4 mt-0.5 rounded" />
			<div class="flex-1 space-y-1.5">
				<Skeleton class="h-4 w-[{60 + (i * 13) % 30}%]" style="width: {60 + (i * 13) % 30}%" />
				<Skeleton class="h-3 w-16" />
			</div>
		</div>
	{/each}
</div>
