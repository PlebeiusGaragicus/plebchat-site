<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	interface Particle {
		x: number;
		y: number;
		vx: number;
		vy: number;
		life: number;
		maxLife: number;
		size: number;
		color: string;
	}

	let canvas: HTMLCanvasElement;
	let ctx: CanvasRenderingContext2D | null;
	let particles: Particle[] = [];
	let animationId: number;
	let mouseX = 0;
	let mouseY = 0;
	let lastMouseX = 0;
	let lastMouseY = 0;

	const colors = [
		'rgba(0, 212, 255, 0.6)',   // cyan
		'rgba(139, 92, 246, 0.5)',  // purple
		'rgba(0, 212, 255, 0.4)',   // cyan dim
	];

	function createParticle(x: number, y: number, vx: number, vy: number): Particle {
		return {
			x,
			y,
			vx: vx * 0.3 + (Math.random() - 0.5) * 2,
			vy: vy * 0.3 + (Math.random() - 0.5) * 2,
			life: 1,
			maxLife: 30 + Math.random() * 20,
			size: 1 + Math.random() * 2,
			color: colors[Math.floor(Math.random() * colors.length)]
		};
	}

	function updateParticles() {
		particles = particles.filter(p => {
			p.x += p.vx;
			p.y += p.vy;
			p.vx *= 0.98;
			p.vy *= 0.98;
			p.life -= 1 / p.maxLife;
			return p.life > 0;
		});
	}

	function drawParticles() {
		if (!ctx || !canvas) return;
		
		ctx.clearRect(0, 0, canvas.width, canvas.height);
		
		for (const p of particles) {
			ctx.beginPath();
			ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
			ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${p.life * 0.6})`);
			ctx.fill();
		}
	}

	function animate() {
		updateParticles();
		drawParticles();
		animationId = requestAnimationFrame(animate);
	}

	function handleMouseMove(e: MouseEvent) {
		mouseX = e.clientX;
		mouseY = e.clientY;
		
		const dx = mouseX - lastMouseX;
		const dy = mouseY - lastMouseY;
		const speed = Math.sqrt(dx * dx + dy * dy);
		
		// Only create particles when mouse is moving
		if (speed > 2) {
			const particleCount = Math.min(Math.floor(speed / 8), 3);
			for (let i = 0; i < particleCount; i++) {
				particles.push(createParticle(mouseX, mouseY, dx, dy));
			}
		}
		
		lastMouseX = mouseX;
		lastMouseY = mouseY;
		
		// Limit particle count
		if (particles.length > 100) {
			particles = particles.slice(-100);
		}
	}

	function handleResize() {
		if (!canvas) return;
		canvas.width = window.innerWidth;
		canvas.height = window.innerHeight;
	}

	onMount(() => {
		if (!browser) return;
		
		ctx = canvas.getContext('2d');
		handleResize();
		
		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('resize', handleResize);
		
		animate();
	});

	onDestroy(() => {
		if (!browser) return;
		
		window.removeEventListener('mousemove', handleMouseMove);
		window.removeEventListener('resize', handleResize);
		cancelAnimationFrame(animationId);
	});
</script>

<canvas 
	bind:this={canvas} 
	id="mouse-trail-canvas"
	class="pointer-events-none fixed inset-0 z-[9999] opacity-60"
></canvas>
