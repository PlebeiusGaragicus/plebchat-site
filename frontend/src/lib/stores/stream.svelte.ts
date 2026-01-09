import { Client, type ThreadState } from '@langchain/langgraph-sdk';
import { get } from 'svelte/store';
import { threads, currentThreadId, type ThreadMessage } from './threads.js';
import { selectedAgent } from './agent.js';

const API_URL = import.meta.env.VITE_LANGGRAPH_API_URL || 'http://localhost:2024';
const ASSISTANT_ID = import.meta.env.VITE_ASSISTANT_ID || 'plebchat';

interface StreamState {
	isLoading: boolean;
	error: string | null;
	currentResponse: string;
}

// Reactive state using Svelte 5 runes
let streamState = $state<StreamState>({
	isLoading: false,
	error: null,
	currentResponse: ''
});

// Create LangGraph client
function createClient(): Client {
	return new Client({
		apiUrl: API_URL
	});
}

export interface PaymentInfo {
	ecash_token: string;
	amount_sats: number;
	mint?: string;
}

export interface SendMessageOptions {
	message: string;
	payment?: PaymentInfo;
	threadId?: string;
}

export async function sendMessage(options: SendMessageOptions): Promise<void> {
	const { message, payment, threadId } = options;
	const agent = get(selectedAgent);
	
	if (!agent) {
		streamState.error = 'No agent selected';
		return;
	}

	streamState.isLoading = true;
	streamState.error = null;
	streamState.currentResponse = '';

	try {
		const client = createClient();
		
		// Create or use existing thread
		let activeThreadId = threadId || get(currentThreadId);
		
		if (!activeThreadId) {
			// Create a new thread in LangGraph
			const lgThread = await client.threads.create();
			activeThreadId = lgThread.thread_id;
			
			// Create local thread record
			const localThread = threads.createThread(agent.id, message);
			currentThreadId.set(localThread.id);
			
			// Store LangGraph thread ID mapping (we'll use the local ID as the main reference)
			// In a real implementation, you might want to store this mapping
		}
		
		// Add human message to local store
		const localThreadId = get(currentThreadId);
		if (localThreadId) {
			threads.addMessage(localThreadId, {
				type: 'human',
				content: message
			});
		}

		// Prepare the input for the agent
		const input = {
			messages: [
				{
					type: 'human',
					content: message
				}
			],
			payment: payment || null
		};

		// Stream the response
		const streamResponse = client.runs.stream(
			activeThreadId,
			ASSISTANT_ID,
			{
				input,
				streamMode: 'messages'
			}
		);

		let fullResponse = '';
		
		// Add placeholder AI message
		if (localThreadId) {
			threads.addMessage(localThreadId, {
				type: 'ai',
				content: ''
			});
		}

		for await (const chunk of streamResponse) {
			if (chunk.event === 'messages/partial') {
				// Handle streaming message chunks
				const messages = chunk.data as Array<{ content?: string; type?: string }>;
				for (const msg of messages) {
					if (msg.type === 'AIMessageChunk' && msg.content) {
						fullResponse += msg.content;
						streamState.currentResponse = fullResponse;
						
						// Update the AI message in the local store
						if (localThreadId) {
							threads.updateLastAiMessage(localThreadId, fullResponse);
						}
					}
				}
			} else if (chunk.event === 'messages/complete') {
				// Message streaming complete
				const messages = chunk.data as Array<{ content?: string; type?: string; tool_calls?: unknown[] }>;
				for (const msg of messages) {
					if (msg.type === 'AIMessage' && msg.content) {
						fullResponse = msg.content as string;
						streamState.currentResponse = fullResponse;
					}
				}
			}
		}

		streamState.isLoading = false;
		
	} catch (error) {
		streamState.isLoading = false;
		streamState.error = error instanceof Error ? error.message : 'Unknown error occurred';
		console.error('Stream error:', error);
	}
}

export function resetStream(): void {
	streamState.isLoading = false;
	streamState.error = null;
	streamState.currentResponse = '';
}

// Export reactive getters
export function getStreamState() {
	return streamState;
}

export function isStreaming(): boolean {
	return streamState.isLoading;
}

export function getStreamError(): string | null {
	return streamState.error;
}

export function getCurrentResponse(): string {
	return streamState.currentResponse;
}
