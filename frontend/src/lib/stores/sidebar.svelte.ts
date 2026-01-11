import { browser } from '$app/environment';

const STORAGE_KEY = 'plebchat-sidebar-open';
const MOBILE_BREAKPOINT = 768;

/**
 * Sidebar state management using Svelte 5 runes
 * Handles separate mobile (drawer) and desktop (fixed panel) states
 */
function createSidebarState() {
	// Desktop panel open state (persisted)
	let desktopOpen = $state(loadDesktopState());
	// Mobile drawer open state (not persisted)
	let mobileOpen = $state(false);
	// Track if we're on mobile
	let isMobile = $state(false);

	// Initialize mobile detection
	if (browser) {
		const mediaQuery = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
		isMobile = mediaQuery.matches;

		mediaQuery.addEventListener('change', (e) => {
			isMobile = e.matches;
			// Close mobile drawer when switching to desktop
			if (!e.matches) {
				mobileOpen = false;
			}
		});

		// Setup keyboard shortcut (Cmd/Ctrl + B)
		window.addEventListener('keydown', handleKeydown);
	}

	function loadDesktopState(): boolean {
		if (!browser) return true; // Default open on desktop
		const stored = localStorage.getItem(STORAGE_KEY);
		return stored === null ? true : stored === 'true';
	}

	function saveDesktopState(open: boolean) {
		if (browser) {
			localStorage.setItem(STORAGE_KEY, String(open));
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'b' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			toggle();
		}
	}

	function toggle() {
		if (isMobile) {
			mobileOpen = !mobileOpen;
		} else {
			desktopOpen = !desktopOpen;
			saveDesktopState(desktopOpen);
		}
	}

	function open() {
		if (isMobile) {
			mobileOpen = true;
		} else {
			desktopOpen = true;
			saveDesktopState(true);
		}
	}

	function close() {
		if (isMobile) {
			mobileOpen = false;
		} else {
			desktopOpen = false;
			saveDesktopState(false);
		}
	}

	function closeMobile() {
		mobileOpen = false;
	}

	return {
		get isOpen() {
			return isMobile ? mobileOpen : desktopOpen;
		},
		get desktopOpen() {
			return desktopOpen;
		},
		get mobileOpen() {
			return mobileOpen;
		},
		set mobileOpen(value: boolean) {
			mobileOpen = value;
		},
		get isMobile() {
			return isMobile;
		},
		toggle,
		open,
		close,
		closeMobile
	};
}

// Create singleton instance
export const sidebar = createSidebarState();
