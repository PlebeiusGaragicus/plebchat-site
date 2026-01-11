<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	let glowElement: HTMLDivElement;
	let mouseX = 0;
	let mouseY = 0;
	let currentX = 0;
	let currentY = 0;
	let animationId: number;

	// Smoothing factor (lower = smoother/slower, higher = snappier)
	const smoothing = 0.08;

	function animate() {
		// Smooth interpolation towards mouse position
		currentX += (mouseX - currentX) * smoothing;
		currentY += (mouseY - currentY) * smoothing;

		if (glowElement) {
			glowElement.style.left = `${currentX}px`;
			glowElement.style.top = `${currentY}px`;
		}

		animationId = requestAnimationFrame(animate);
	}

	function handleMouseMove(e: MouseEvent) {
		mouseX = e.clientX;
		mouseY = e.clientY;
	}

	onMount(() => {
		if (!browser) return;

		// Initialize position
		currentX = window.innerWidth / 2;
		currentY = window.innerHeight / 2;
		mouseX = currentX;
		mouseY = currentY;

		window.addEventListener('mousemove', handleMouseMove);
		animate();
	});

	onDestroy(() => {
		if (!browser) return;
		window.removeEventListener('mousemove', handleMouseMove);
		cancelAnimationFrame(animationId);
	});
</script>

<div
	bind:this={glowElement}
	class="pointer-events-none fixed z-0 -translate-x-1/2 -translate-y-1/2"
	style="
		width: 600px;
		height: 600px;
		background: radial-gradient(
			circle,
			rgba(0, 212, 255, 0.08) 0%,
			rgba(139, 92, 246, 0.04) 30%,
			transparent 70%
		);
		filter: blur(60px);
	"
></div>
