import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

export interface ThreadMessage {
	id: string;
	type: 'human' | 'ai' | 'tool';
	content: string;
	timestamp: number;
	toolCalls?: ToolCall[];
}

export interface ToolCall {
	id: string;
	name: string;
	args: Record<string, unknown>;
	result?: string;
}

export interface Thread {
	id: string;
	agentId: string;
	title: string;
	createdAt: number;
	updatedAt: number;
	messages: ThreadMessage[];
	promptCount: number;
	langgraphThreadId?: string; // Maps to LangGraph server thread ID
}

const STORAGE_KEY = 'plebchat-threads';

function loadThreads(): Thread[] {
	if (!browser) return [];
	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		return stored ? JSON.parse(stored) : [];
	} catch {
		return [];
	}
}

function saveThreads(threads: Thread[]): void {
	if (!browser) return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
}

function createThreadsStore() {
	const { subscribe, set, update } = writable<Thread[]>(loadThreads());

	// Auto-save to localStorage whenever the store changes
	subscribe((threads) => {
		saveThreads(threads);
	});

	return {
		subscribe,
		
		createThread: (agentId: string, firstMessage?: string, langgraphThreadId?: string): Thread => {
			const newThread: Thread = {
				id: crypto.randomUUID(),
				agentId,
				title: firstMessage?.slice(0, 50) || 'New Chat',
				createdAt: Date.now(),
				updatedAt: Date.now(),
				messages: [],
				promptCount: 0,
				langgraphThreadId
			};
			
			update(threads => [newThread, ...threads]);
			return newThread;
		},

		setLanggraphThreadId: (threadId: string, langgraphThreadId: string) => {
			update(threads => {
				return threads.map(thread => {
					if (thread.id !== threadId) return thread;
					return { ...thread, langgraphThreadId };
				});
			});
		},

		getLanggraphThreadId: (threadId: string): string | undefined => {
			const thread = get({ subscribe }).find(t => t.id === threadId);
			return thread?.langgraphThreadId;
		},

		addMessage: (threadId: string, message: Omit<ThreadMessage, 'id' | 'timestamp'>) => {
			update(threads => {
				return threads.map(thread => {
					if (thread.id !== threadId) return thread;
					
					const newMessage: ThreadMessage = {
						...message,
						id: crypto.randomUUID(),
						timestamp: Date.now()
					};
					
					return {
						...thread,
						messages: [...thread.messages, newMessage],
						updatedAt: Date.now(),
						promptCount: message.type === 'human' ? thread.promptCount + 1 : thread.promptCount,
						// Update title if this is the first human message
						title: thread.messages.length === 0 && message.type === 'human' 
							? message.content.slice(0, 50) 
							: thread.title
					};
				});
			});
		},

		updateLastAiMessage: (threadId: string, content: string) => {
			update(threads => {
				return threads.map(thread => {
					if (thread.id !== threadId) return thread;
					
					const messages = [...thread.messages];
					const lastAiIndex = messages.findLastIndex(m => m.type === 'ai');
					
					if (lastAiIndex >= 0) {
						messages[lastAiIndex] = {
							...messages[lastAiIndex],
							content
						};
					}
					
					return { ...thread, messages, updatedAt: Date.now() };
				});
			});
		},

		deleteThread: (threadId: string) => {
			update(threads => threads.filter(t => t.id !== threadId));
		},

		getThread: (threadId: string): Thread | undefined => {
			return get({ subscribe }).find(t => t.id === threadId);
		},

		// Sync messages from server - replaces local messages with server state
		syncMessagesFromServer: (threadId: string, messages: ThreadMessage[]) => {
			update(threads => {
				return threads.map(thread => {
					if (thread.id !== threadId) return thread;
					
					// Count human messages for promptCount
					const promptCount = messages.filter(m => m.type === 'human').length;
					
					// Update title from first human message if needed
					const firstHuman = messages.find(m => m.type === 'human');
					const title = firstHuman ? firstHuman.content.slice(0, 50) : thread.title;
					
					return {
						...thread,
						messages,
						promptCount,
						title,
						updatedAt: Date.now()
					};
				});
			});
		},

		clear: () => {
			set([]);
		}
	};
}

export const threads = createThreadsStore();

// Current active thread ID
export const currentThreadId = writable<string | null>(null);

// Derived store for current thread
export const currentThread = derived(
	[threads, currentThreadId],
	([$threads, $currentThreadId]) => {
		if (!$currentThreadId) return null;
		return $threads.find(t => t.id === $currentThreadId) || null;
	}
);

// Get threads for a specific agent (returns a derived store)
export function getThreadsForAgent(agentId: string) {
	return derived(threads, ($threads) => 
		$threads.filter(t => t.agentId === agentId)
			.sort((a, b) => b.updatedAt - a.updatedAt)
	);
}

// Filter threads by agent ID (pure function for use with Svelte 5 runes)
export function filterThreadsByAgent(allThreads: Thread[], agentId: string | null): Thread[] {
	if (!agentId) return [];
	return allThreads
		.filter(t => t.agentId === agentId)
		.sort((a, b) => b.updatedAt - a.updatedAt);
}
