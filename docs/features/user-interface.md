# User Interface

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Browser                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         +layout.svelte                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │     Navbar      │  │   MouseTrail    │  │  Toast Notifs   │   │  │
│  │  │  (AgentDropdown │  │   (glow effect) │  │  (svelte-sonner)│   │  │
│  │  │   + Cyphertap)  │  │                 │  │                 │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                          +page.svelte                              │  │
│  │                                                                    │  │
│  │   ┌──────────────────┐          ┌──────────────────────────────┐  │  │
│  │   │  ThreadSidebar   │          │  WelcomePage (if no agent)   │  │  │
│  │   │  - Thread list   │          │  - Feature grid              │  │  │
│  │   │  - New chat      │          │  - Agent selection           │  │  │
│  │   │  - Delete        │          └──────────────────────────────┘  │  │
│  │   └──────────────────┘                       OR                   │  │
│  │                                 ┌──────────────────────────────┐  │  │
│  │                                 │  ChatContainer (if agent)    │  │  │
│  │                                 │  ┌────────────────────────┐  │  │  │
│  │                                 │  │  ChatMessage (list)    │  │  │  │
│  │                                 │  │  - User/AI/Tool types  │  │  │  │
│  │                                 │  │  - ToolCallDisplay     │  │  │  │
│  │                                 │  └────────────────────────┘  │  │  │
│  │                                 │  ┌────────────────────────┐  │  │  │
│  │                                 │  │  ChatInput             │  │  │  │
│  │                                 │  │  - Cost display        │  │  │  │
│  │                                 │  │  - Send button         │  │  │  │
│  │                                 │  └────────────────────────┘  │  │  │
│  │                                 └──────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                    ┌───────────────┴───────────────┐                    │
│                    ▼                               ▼                    │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │       Svelte Stores         │  │         Cyphertap               │  │
│  │  ┌───────────────────────┐  │  │  - Nostr login                  │  │
│  │  │ agent.ts (selection)  │  │  │  - Ecash wallet                 │  │
│  │  │ threads.ts (history)  │  │  │  - Token generation             │  │
│  │  │ stream.svelte.ts      │  │  │  - Balance management           │  │
│  │  └───────────────────────┘  │  └─────────────────────────────────┘  │
│  └─────────────────────────────┘                                        │
│                    │                                                     │
└────────────────────┼─────────────────────────────────────────────────────┘
                     │
                     ▼
        ┌───────────────────────┐
        │   LangGraph Backend   │
        │   (streaming API)     │
        └───────────────────────┘
```

---

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| SvelteKit | 2.49.1 | Application framework |
| Svelte | 5.45.6 | Reactive UI with runes |
| Tailwind CSS | 4.0.0 | Utility-first styling |
| TypeScript | 5.9.3 | Type safety |
| LangGraph SDK | 0.0.43 | AI agent streaming |
| Cyphertap | local | Bitcoin/ecash wallet |
| Bits UI | 2.9.4 | Accessible components |
| Lucide Svelte | 0.515.0 | Icon library |
| Svelte Sonner | 1.0.5 | Toast notifications |

### Build Configuration

The frontend is a **pure client-side SPA** with no server-side rendering:

| Setting | Value | Description |
|---------|-------|-------------|
| Adapter | `@sveltejs/adapter-static` | Generates static files only |
| SSR | `false` | All rendering happens in browser |
| Prerender | `true` | Generates HTML shell at build time |
| Fallback | `index.html` | All routes serve the same shell |

**Build output:** Static files in `build/` directory, deployable to any static host (Nginx, S3, Cloudflare Pages, GitHub Pages, etc.).

---

## Application Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │   Select    │     │   Send      │     │   Receive   │
│   Visits    │────▶│   Agent     │────▶│   Message   │────▶│   Response  │
│   Site      │     │             │     │   + Payment │     │   Stream    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  WelcomePage         ChatContainer      Cyphertap          ChatMessage
  (feature grid)      (empty state)      generates          (streaming
                                         ecash token        with cursor)
```

### User Journey

1. **Landing**: User sees WelcomePage with feature grid (Pay Per Use, Self Custody, No Accounts, etc.)
2. **Agent Selection**: User selects an AI agent from the grid or dropdown
3. **Chat Interface**: ChatContainer displays with input field showing prompt cost
4. **Payment**: On send, Cyphertap generates ecash token for the prompt cost
5. **Streaming**: LangGraph streams response chunks, displayed in real-time
6. **History**: Conversation saved to LocalStorage, accessible via ThreadSidebar

---

## Components

### Overview Table

| Component | Location | Purpose |
|-----------|----------|---------|
| WelcomePage | `lib/components/WelcomePage.svelte` | Landing page with features and agent grid |
| ChatContainer | `lib/components/chat/ChatContainer.svelte` | Main chat interface with messages and input |
| ChatInput | `lib/components/chat/ChatInput.svelte` | Auto-expanding textarea with cost display |
| ChatMessage | `lib/components/chat/ChatMessage.svelte` | Message bubble with avatar and tool calls |
| ToolCallDisplay | `lib/components/chat/ToolCallDisplay.svelte` | Expandable tool execution details |
| Navbar | `lib/components/nav/Navbar.svelte` | Top navigation with logo and wallet |
| AgentDropdown | `lib/components/nav/AgentDropdown.svelte` | Agent selection dropdown menu |
| ThreadSidebar | `lib/components/sidebar/ThreadSidebar.svelte` | Chat history sidebar with thread list |
| MouseTrail | `lib/components/effects/MouseTrail.svelte` | Animated mouse-following glow effect |

### Component Details

#### WelcomePage

The landing page shown when no agent is selected.

**Features:**
- Hero section with headline "AI Chat, Pay-Per-Use"
- 6-item feature grid:
  - Pay Per Use (Bitcoin micropayments)
  - Self Custody (ecash stored on device)
  - No Accounts (Nostr-based identity)
  - Permissionless (no restrictions)
  - Local Storage (no data collection)
  - Instant Payments (no confirmation wait)
- Agent selection grid with availability indicators
- Responsive layout (1-3 columns based on viewport)

#### ChatContainer

The main chat interface displayed after agent selection.

**Features:**
- Empty state with agent info when no messages
- Scrollable message history with auto-scroll
- Bottom-fixed input area
- Error handling with toast notifications
- Refund token auto-redemption on payment failures
- Cost calculation based on agent and prompt count

**Cost Logic:**
```
First prompt: agent.initialCost (e.g., 50 sats)
Subsequent: agent.additionalCost (e.g., 10 sats)
```

#### ChatInput

Floating message input with payment cost display.

**Features:**
- Floating oval design positioned over chat area
- Glassmorphism effect (backdrop blur, semi-transparent)
- Auto-expanding textarea (max 150px height)
- Smart Enter handling (Enter sends, Shift+Enter newline)
- Centered cost indicator pill (floats above input)
- Centered low balance warning pill (amber color when insufficient)
- Settings button (circular, opens agent configuration)
- Send button (circular with hover scale, glow effects)
- Disabled states for: no agent, insufficient balance, streaming

#### ChatMessage

Individual message display with type differentiation.

**Message Types:**

| Type | Avatar Color | Bubble Background | Label |
|------|--------------|-------------------|-------|
| human | Purple (`#7c3aed`) | Purple tint (`purple-dim/20`) | "You" |
| ai | Orange gradient | Elevated (`bg-elevated`) | "PlebChat" |
| tool | Gray | - | Tool name |

**Features:**
- Transparent row backgrounds (no visible boxes when mouse effect passes)
- Streaming cursor animation for empty AI messages
- Tool call expansion via ToolCallDisplay
- Copy button on hover
- Pre-wrap text formatting
- Responsive sizing

#### ToolCallDisplay

Expandable visualization of agent tool executions.

**Features:**
- Collapsible with chevron indicator
- Tool name with status icon (checkmark for complete)
- Arguments display (JSON formatted, monospace)
- Result display when available
- Syntax highlighting colors

#### Navbar

Fixed top navigation bar.

**Features:**
- PlebChat logo with Zap icon (links to welcome)
- AgentDropdown for agent selection
- Testing mode badge (shows when active)
- Cyphertap wallet component
- Sticky positioning (z-index 50)

#### AgentDropdown

Dropdown menu for agent selection.

**Features:**
- "Help me choose" option (shows WelcomePage)
- Agent list with:
  - Emoji and name
  - Lock icon for unavailable agents
  - Cost display (initial + per prompt)
  - Checkmark for selected
- Click-outside to close
- Keyboard accessible

#### ThreadSidebar

Collapsible sidebar for chat history management.

**Features:**
- CSS-based responsive rendering (both mobile and desktop markup always rendered)
- Desktop (`md:` and up): Fixed sidebar panel with toggle button
- Mobile (below `md:`): Drawer overlay (vaul-svelte) with backdrop
- "New Chat" button
- Thread list with:
  - Title (first 50 chars of first message)
  - Relative timestamp (Today, Yesterday, Xd ago)
  - Delete button with confirmation
- Agent-specific filtering
- Auto-collapse on mobile after selection
- Empty states for no agent or no threads

#### MouseTrail

Visual effect that follows mouse movement.

**Features:**
- Radial gradient glow (orange to purple, matching theme)
- 500x500px blur effect with 50px filter
- Fast CSS transition (60ms) for responsive tracking
- Svelte 5 `$state` reactivity for position updates
- Opacity: 18% orange core, 12% purple fade

---

## State Management

All state is managed with Svelte stores and persisted to LocalStorage.

### Agent Store

**File:** `lib/stores/agent.ts`

Manages the currently selected AI agent.

**Key Features:**
- LocalStorage persistence (`plebchat-selected-agent`)
- Predefined agent configurations
- Agent selection with auto-save
- "Clear" action to return to welcome

**Agent Interface:**
```typescript
interface Agent {
  id: string;
  name: string;
  emoji: string;
  description: string;
  available: boolean;
  initialCost: number;      // sats for first prompt
  additionalCost: number;   // sats per subsequent prompt
  capabilities: string[];
  fileUpload: 'none' | 'images' | 'pdf' | 'all';
  historyEnabled: boolean;
}
```

### Threads Store

**File:** `lib/stores/threads.ts`

Manages chat conversation history.

**Key Features:**
- LocalStorage persistence (`plebchat-threads`)
- Thread creation with first message as title
- Message streaming support (partial updates)
- Tool call tracking
- Prompt counting for cost calculation
- LangGraph thread ID mapping
- Thread deletion with fallback

**Key Types:**
```typescript
interface Thread {
  id: string;
  agentId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ThreadMessage[];
  promptCount: number;
  langGraphThreadId?: string;
}

interface ThreadMessage {
  id: string;
  type: 'human' | 'ai' | 'tool';
  content: string;
  timestamp: number;
  toolCalls?: ToolCall[];
}
```

### Stream Store

**File:** `lib/stores/stream.svelte.ts`

Manages LangGraph API communication and streaming.

**Key Features:**
- Svelte 5 runes for reactivity
- Debug mode flag (VITE_DEBUG=1 shows testnet badge)
- Loading/streaming state
- Error capture and display
- Refund token management
- LangGraph integration:
  - Dynamic thread creation
  - Dual stream modes ('messages' + 'values')
  - AI message and tool call handling

**Configuration:**
```typescript
const LANGGRAPH_API_URL = import.meta.env.VITE_LANGGRAPH_API_URL
  || 'http://localhost:2024';
const ASSISTANT_ID = import.meta.env.VITE_ASSISTANT_ID
  || 'plebchat';
```

---

## AI Agents

Five agents are configured, with only PlebChat currently active.

| Agent | Emoji | Status | Initial | Per Prompt | Features |
|-------|-------|--------|---------|------------|----------|
| PlebChat | 🗣️🤖💭 | **Active** | 50 sats | 10 sats | Simple chat, history enabled |
| Deep Research | 🌎📚🔭 | Coming Soon | 150 sats | 200 sats | Internet research |
| Socratic Coach | ☕️🧠💭 | Coming Soon | 50 sats | 0 sats | Guided learning, image upload |
| TLDR Summarizer | 📖🤨❓ | Coming Soon | 150 sats | 200 sats | Document summarization |
| NSFW | 🙉🙈🙊 | Coming Soon | 70 sats | 20 sats | Unrestricted, no history |

### Agent Capabilities

Each agent defines its capabilities and file upload support:

| Agent | Capabilities | File Upload |
|-------|-------------|-------------|
| PlebChat | chat | none |
| Deep Research | research, analysis | none |
| Socratic Coach | teaching, discussion | images |
| TLDR Summarizer | summarization | pdf |
| NSFW | unrestricted | none |

---

## Payment Integration

### Cyphertap Wallet

The frontend integrates with Cyphertap for Bitcoin/ecash payments.

**Features:**
- Nostr-based login (no accounts)
- Ecash token storage in browser
- Balance display in navbar
- Token generation for prompts
- Token redemption for refunds

### Payment Flow

```
1. User enters message
2. ChatInput calculates cost based on agent + prompt count
3. User clicks Send
4. ChatContainer calls cyphertap.generateEcashToken(cost)
5. Token sent with message to LangGraph
6. On success: message displays, prompt count increments
7. On failure: refund token returned, auto-redeemed
```

### Debug Mode

When `DEBUG_MODE` is enabled (via `VITE_DEBUG=1` in `.env.development`):
- Debug badge shown in navbar to indicate testnet environment
- Useful for development with FakeWallet mint
- Full agent pricing is always used

---

## Design System

### Color Palette

| Variable | Value | Usage |
|----------|-------|-------|
| `--color-bg-primary` | `#030305` | Main background (ultra-dark) |
| `--color-bg-secondary` | `#08080c` | Secondary surfaces |
| `--color-bg-tertiary` | `#0e0e14` | Tertiary surfaces |
| `--color-bg-elevated` | `#16161e` | Cards, modals |
| `--color-accent-primary` | `#f97316` | Primary accent (orange) |
| `--color-accent-dim` | `#ea580c` | Dimmed accent |
| `--color-purple-accent` | `#a855f7` | Secondary accent (purple) |
| `--color-purple-dim` | `#7c3aed` | Dimmed purple |
| `--color-green-success` | `#22c55e` | Success states |
| `--color-amber-warning` | `#fbbf24` | Warning states |
| `--color-red-error` | `#ef4444` | Error states |
| `--color-text-primary` | `#ffffff` | Main text |
| `--color-text-secondary` | `#b4b4bc` | Secondary text |
| `--color-text-muted` | `#6b6b78` | Muted text |
| `--color-border-default` | `#2a2a38` | Default borders |
| `--color-border-hover` | `#3d3d50` | Hover borders |
| `--color-border-bright` | `#4a4a60` | Bright borders |

### Custom CSS Features

| Class/Animation | Purpose |
|-----------------|---------|
| `.bg-digital` | Grid pattern background (purple/orange subtle lines) |
| `.glow-input` | Animated border glow on focus |
| `@keyframes glow-pulse` | 3s pulsing glow |
| `@keyframes border-flow` | Flowing gradient animation |
| `.animate-fade-in` | Entrance fade animation |
| `.btn-primary` | Gradient orange button |
| `.btn-ghost` | Transparent ghost button |

### Typography

| Font | Usage |
|------|-------|
| Inter | Primary sans-serif |
| JetBrains Mono | Code and monospace |

### Responsive Breakpoints

| Breakpoint | Width | Usage |
|------------|-------|-------|
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |

---

## Features Not Yet Implemented

### Coming Soon Agents
- **Deep Research**: Internet search and analysis
- **Socratic Coach**: Interactive guided learning
- **TLDR Summarizer**: PDF and document summarization
- **NSFW**: Unrestricted conversation mode

### Planned Features
- **File Upload**: Image and PDF attachment support (UI exists, backend pending)
- **Agent Settings Modal**: Per-session agent configuration
- **Message Editing**: Edit sent messages
- **Message Reactions**: Thumbs up/down for feedback
- **Export Chat**: Download conversation history


---

## File Structure

```
frontend/src/
├── routes/
│   ├── +layout.svelte      # Global layout (navbar, effects, toasts)
│   ├── +layout.ts          # SPA config: ssr=false, prerender=true
│   └── +page.svelte        # Main page (welcome or chat)
├── lib/
│   ├── components/
│   │   ├── WelcomePage.svelte
│   │   ├── chat/
│   │   │   ├── ChatContainer.svelte
│   │   │   ├── ChatInput.svelte
│   │   │   ├── ChatMessage.svelte
│   │   │   └── ToolCallDisplay.svelte
│   │   ├── nav/
│   │   │   ├── Navbar.svelte
│   │   │   └── AgentDropdown.svelte
│   │   ├── sidebar/
│   │   │   └── ThreadSidebar.svelte
│   │   └── effects/
│   │       └── MouseTrail.svelte
│   ├── stores/
│   │   ├── agent.ts
│   │   ├── threads.ts
│   │   ├── sidebar.svelte.ts
│   │   └── stream.svelte.ts
│   ├── assets/
│   │   └── favicon.svg
│   └── utils.ts            # cn() class merge utility
├── app.css                 # Global styles + design system
├── app.d.ts               # Type definitions
└── app.html               # HTML template
```
