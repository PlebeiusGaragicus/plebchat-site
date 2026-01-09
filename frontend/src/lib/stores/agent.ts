import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export interface Agent {
	id: string;
	name: string;
	emoji: string;
	description: string;
	initialCost: number;
	additionalCost: number;
	fileUpload: 'none' | 'images' | 'pdf' | 'all';
	available: boolean;
}

export const AGENTS: Agent[] = [
	{
		id: 'plebchat',
		name: 'PlebChat',
		emoji: '🗣️🤖💭',
		description: 'Simple AI chat - no fluff - history enabled for long conversations.',
		initialCost: 50,
		additionalCost: 10,
		fileUpload: 'none',
		available: true
	},
	{
		id: 'deep-research',
		name: 'Deep Research',
		emoji: '🌎📚🔭',
		description: 'Deep research agent for comprehensive internet research.',
		initialCost: 150,
		additionalCost: 200,
		fileUpload: 'none',
		available: false
	},
	{
		id: 'socratic-coach',
		name: 'Socratic Coach',
		emoji: '☕️🧠💭',
		description: 'Guided learning through Socratic questioning.',
		initialCost: 50,
		additionalCost: 0, // Unable to prompt again
		fileUpload: 'images',
		available: false
	},
	{
		id: 'tldr-summarizer',
		name: 'TLDR Summarizer',
		emoji: '📖🤨❓',
		description: 'Summarize long documents quickly.',
		initialCost: 150,
		additionalCost: 200,
		fileUpload: 'pdf',
		available: false
	},
	{
		id: 'nsfw',
		name: 'NSFW',
		emoji: '🙉🙈🙊',
		description: 'Unrestricted conversations. No history saved.',
		initialCost: 70,
		additionalCost: 20,
		fileUpload: 'none',
		available: false
	}
];

const STORAGE_KEY = 'plebchat-selected-agent';

function getStoredAgentId(): string | null {
	if (!browser) return null;
	return localStorage.getItem(STORAGE_KEY);
}

function setStoredAgentId(id: string): void {
	if (!browser) return;
	localStorage.setItem(STORAGE_KEY, id);
}

// Create the selected agent store
function createSelectedAgentStore() {
	const storedId = getStoredAgentId();
	const initialAgent = storedId 
		? AGENTS.find(a => a.id === storedId && a.available) || null 
		: null;
	
	const { subscribe, set, update } = writable<Agent | null>(initialAgent);

	return {
		subscribe,
		select: (agent: Agent) => {
			if (agent.available) {
				setStoredAgentId(agent.id);
				set(agent);
			}
		},
		clear: () => {
			if (browser) localStorage.removeItem(STORAGE_KEY);
			set(null);
		}
	};
}

export const selectedAgent = createSelectedAgentStore();

// Derived store for available agents only
export const availableAgents = derived(
	[], 
	() => AGENTS.filter(a => a.available)
);

// Get agent by ID helper
export function getAgentById(id: string): Agent | undefined {
	return AGENTS.find(a => a.id === id);
}
