import { Client, type ThreadState } from '@langchain/langgraph-sdk';
import { get } from 'svelte/store';
import { threads, currentThreadId, type ThreadMessage } from './threads.js';
import { selectedAgent } from './agent.js';

const API_URL = import.meta.env.VITE_LANGGRAPH_API_URL || 'http://localhost:2024';
const ASSISTANT_ID = import.meta.env.VITE_ASSISTANT_ID || 'plebchat';

// Testing mode: When enabled, all prompts cost 1 sat regardless of agent pricing
// Set to false for production
export const TESTING_MODE = true;
export const TESTING_MODE_COST = 1; // Cost per prompt in testing mode

interface StreamState {
	isLoading: boolean;
	error: string | null;
	currentResponse: string;
	refundToken: string | null;  // Token returned for refund on failure
}

// Reactive state using Svelte 5 runes
let streamState = $state<StreamState>({
	isLoading: false,
	error: null,
	currentResponse: '',
	refundToken: null
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
	streamState.refundToken = null;

	try {
		const client = createClient();
		
		// Get or create the local thread ID
		let localThreadId = threadId || get(currentThreadId);
		let langgraphThreadId: string | undefined;
		
		if (!localThreadId) {
			// Create a new thread in LangGraph first
			const lgThread = await client.threads.create();
			langgraphThreadId = lgThread.thread_id;
			
			// Create local thread record with the LangGraph thread ID
			const localThread = threads.createThread(agent.id, message, langgraphThreadId);
			localThreadId = localThread.id;
			currentThreadId.set(localThreadId);
		} else {
			// Get existing LangGraph thread ID from local store
			langgraphThreadId = threads.getLanggraphThreadId(localThreadId);
			
			// If no LangGraph thread exists yet, create one
			if (!langgraphThreadId) {
				const lgThread = await client.threads.create();
				langgraphThreadId = lgThread.thread_id;
				threads.setLanggraphThreadId(localThreadId, langgraphThreadId);
			}
		}
		
		// Add human message to local store
		threads.addMessage(localThreadId, {
			type: 'human',
			content: message
		});

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

		// Stream the response using the LangGraph thread ID
		// Use both 'messages' and 'values' modes to get streaming + final state
		const streamResponse = client.runs.stream(
			langgraphThreadId,
			ASSISTANT_ID,
			{
				input,
				streamMode: ['messages', 'values']
			}
		);

		let fullResponse = '';
		let hasError = false;
		let aiMessageAdded = false;

		for await (const chunk of streamResponse) {
			if (chunk.event === 'messages/partial') {
				// Add placeholder AI message on first chunk
				if (!aiMessageAdded) {
					threads.addMessage(localThreadId, {
						type: 'ai',
						content: ''
					});
					aiMessageAdded = true;
				}
				
				// Handle streaming message chunks - data contains accumulated content
				const messages = chunk.data as Array<{ content?: string; type?: string }>;
				for (const msg of messages) {
					// Check for AI message types (handle variations in type names)
					const isAiMessage = msg.type === 'AIMessageChunk' || 
										msg.type === 'ai' || 
										msg.type?.includes('AI');
					if (isAiMessage && msg.content) {
						// messages/partial contains accumulated content, not delta
						fullResponse = msg.content as string;
						streamState.currentResponse = fullResponse;
						
						// Update the AI message in the local store
						threads.updateLastAiMessage(localThreadId, fullResponse);
					}
				}
			} else if (chunk.event === 'messages/complete') {
				// Add AI message if not already added
				if (!aiMessageAdded) {
					threads.addMessage(localThreadId, {
						type: 'ai',
						content: ''
					});
					aiMessageAdded = true;
				}
				
				// Message streaming complete
				const messages = chunk.data as Array<{ content?: string; type?: string; tool_calls?: unknown[] }>;
				for (const msg of messages) {
					// Check for AI message types (handle variations in type names)
					const isAiMessage = msg.type === 'AIMessage' || 
										msg.type === 'ai' || 
										msg.type?.includes('AI');
					if (isAiMessage && msg.content) {
						fullResponse = msg.content as string;
						streamState.currentResponse = fullResponse;
						
						// Update the AI message in the local store
						threads.updateLastAiMessage(localThreadId, fullResponse);
					}
				}
			} else if (chunk.event === 'values') {
				// Final state from the agent - check for errors and refund tokens
				const state = chunk.data as {
					error?: string | null;
					refund?: boolean;
					refund_token?: string | null;
					messages?: Array<{ content?: string; type?: string }>;
				};
				
				// Check for payment/processing errors
				if (state.error) {
					hasError = true;
					streamState.error = state.error;
					console.error('[Stream] Agent error:', state.error);
				}
				
				// Check for refund token
				if (state.refund && state.refund_token) {
					streamState.refundToken = state.refund_token;
					console.log('[Stream] Refund token received, will attempt auto-redeem');
				}
				
				// Also capture the final message if not streamed
				if (state.messages && state.messages.length > 0) {
					const lastMsg = state.messages[state.messages.length - 1];
					if ((lastMsg.type === 'ai' || lastMsg.type === 'AIMessage') && lastMsg.content) {
						if (!aiMessageAdded) {
							threads.addMessage(localThreadId, {
								type: 'ai',
								content: lastMsg.content
							});
							aiMessageAdded = true;
						} else {
							threads.updateLastAiMessage(localThreadId, lastMsg.content);
						}
						fullResponse = lastMsg.content;
						streamState.currentResponse = fullResponse;
					}
				}
			}
		}

		streamState.isLoading = false;
		
		// Return info about whether we have a refund token
		if (hasError && streamState.refundToken) {
			console.log('[Stream] Request failed with refundable token');
		}
		
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
	streamState.refundToken = null;
}

// Clear the refund token after it's been processed
export function clearRefundToken(): void {
	streamState.refundToken = null;
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

export function getRefundToken(): string | null {
	return streamState.refundToken;
}
