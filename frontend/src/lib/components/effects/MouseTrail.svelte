<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	let glowElement: HTMLDivElement;
	let mouseX = $state(0);
	let mouseY = $state(0);
	let animationId: number;

	function handleMouseMove(e: MouseEvent) {
		mouseX = e.clientX;
		mouseY = e.clientY;
	}

	onMount(() => {
		if (!browser) return;

		// Initialize at center
		mouseX = window.innerWidth / 2;
		mouseY = window.innerHeight / 2;

		window.addEventListener('mousemove', handleMouseMove);
	});

	onDestroy(() => {
		if (!browser) return;
		window.removeEventListener('mousemove', handleMouseMove);
	});
</script>

<div
	bind:this={glowElement}
	class="pointer-events-none fixed z-0 -translate-x-1/2 -translate-y-1/2"
	style="
		left: {mouseX}px;
		top: {mouseY}px;
		width: 500px;
		height: 500px;
		background: radial-gradient(
			circle,
			rgba(249, 115, 22, 0.18) 0%,
			rgba(168, 85, 247, 0.12) 35%,
			transparent 65%
		);
		filter: blur(50px);
		transition: left 0.06s ease-out, top 0.06s ease-out;
	"
></div>
