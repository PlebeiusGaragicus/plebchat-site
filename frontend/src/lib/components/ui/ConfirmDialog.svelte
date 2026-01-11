<script lang="ts">
	import { Dialog } from 'bits-ui';
	import { AlertTriangle, X } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';

	interface Props {
		open: boolean;
		title?: string;
		description?: string;
		confirmLabel?: string;
		cancelLabel?: string;
		variant?: 'default' | 'destructive';
		onConfirm: () => void;
		onCancel?: () => void;
	}

	let {
		open = $bindable(false),
		title = 'Are you sure?',
		description = 'This action cannot be undone.',
		confirmLabel = 'Confirm',
		cancelLabel = 'Cancel',
		variant = 'default',
		onConfirm,
		onCancel
	}: Props = $props();

	function handleConfirm() {
		onConfirm();
		open = false;
	}

	function handleCancel() {
		onCancel?.();
		open = false;
	}

	function handleOpenChange(isOpen: boolean) {
		if (!isOpen) {
			handleCancel();
		}
	}
</script>

<Dialog.Root bind:open onOpenChange={handleOpenChange}>
	<Dialog.Portal>
		<Dialog.Overlay
			class="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
		/>
		<Dialog.Content
			class="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[var(--color-border-hover)] bg-[var(--color-bg-secondary)] p-6 shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
		>
			<!-- Header -->
			<div class="flex items-start gap-3 mb-4">
				{#if variant === 'destructive'}
					<div
						class="flex-shrink-0 w-10 h-10 rounded-full bg-[var(--color-red-error)]/20 flex items-center justify-center"
					>
						<AlertTriangle class="w-5 h-5 text-[var(--color-red-error)]" />
					</div>
				{/if}
				<div class="flex-1">
					<Dialog.Title class="text-lg font-semibold text-[var(--color-text-primary)]">
						{title}
					</Dialog.Title>
					<Dialog.Description class="text-sm text-[var(--color-text-muted)] mt-1">
						{description}
					</Dialog.Description>
				</div>
				<Dialog.Close
					class="p-1 rounded-md hover:bg-[var(--color-bg-elevated)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
				>
					<X class="w-4 h-4" />
				</Dialog.Close>
			</div>

			<!-- Footer -->
			<div class="flex justify-end gap-2 mt-6">
				<Dialog.Close class="btn btn-ghost">{cancelLabel}</Dialog.Close>
				<button
					onclick={handleConfirm}
					class={cn(
						'btn',
						variant === 'destructive'
							? 'bg-[var(--color-red-error)] hover:bg-[var(--color-red-error)]/80 text-white'
							: 'btn-primary'
					)}
				>
					{confirmLabel}
				</button>
			</div>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
