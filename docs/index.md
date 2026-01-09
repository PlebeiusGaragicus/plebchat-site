# What is PlebChat?

⚠️ Coding agents must ALWAYS read [their instructions](../README.md).

---

## Core Product

**PlebChat** is a simple AI chat web application that demonstrates:

 - A Svelte 5 client-side UI in `frontend/` with a "CypherTap" library used to handle user login, bitcoin ecash wallet and micropayments for pay-per-use AI usage.
 - A Python3.12 FastAPI `backend/` used to validate and redeem ecash tokens
 - LangGraph `agents/` are simple LLM graphs that verify ecash before execution.

---

- **Nostr Protocol:**
    - **Users** are just simply public/private key pairs - no usernames/passwords. Usage of a NIP-07 browser extention elevates this experience even further.
    - **Just works** - Nostr protocol is used "under the hood" and should be largely invisible to the user. We aim for an experience that *"just works"* with only the "advanced user" suspecting usage of the nostr protocol.

- **Client-Side Storage:**
    - **Local Browser Storage:** All application data is stored in the user's browser, you own your data.
    - **Progressive web app** - Avoid "app store" ecosystem lock-in - we don't need approval to publish freedom tech apps.

- **eCash Payments:**
    - **Bitcoin payments:** *any human* can pay for this service without risk of regulations locking them out.
    - **Pay-per-use** AI features avoid subscriptions therefore the over-charging of users who don't maximize their monthly usage.
    - **Self-custody** prevents risk of centralized theft of user funds - private keys are stored on user's devices.


## Features:

 * A top navbar shows "PlebChat" in the top left corner with a dropdown/popover to its right that allows the user to select an agent.  A "Help me choose" is available which shows an FAQ in the main content area with links to each suggested agent.
 * On right edge of the top navbar we place our CypherTap component.  When logged out the main content area shows "welcome" to plebchat content with a beautiful explanation of the site.  Once logged in we select the latest agent selected in the dropdown - if site previously visited - and the "help me choose" option otherwise.
 * The main content area shows a collapsing sidepanel that shows preveious chat threads for the selected agent (if saved).
 * Once an agent is selected a beautiful and minimal interface allows them to enter a prompt. Faint mouse trails are enabled which appear to energize the digital/binary background behind them. The input box appears to glow and invites the user to ask, learn and engage.  A settings gear icon embedded in the prompt input box activates a modal which allows the user to adjust the configuration of the currently selected agent, with a "Use settings for this chat" and "Save agent configuration" options.
 * Similarly to the example repositories, the agent's tool calls displayed inline in the chat history.


 ## Agents

### PlebChat 🗣️🤖💭

This graph is a single LLM call - no fluf - history is appended to enable long conversations.

> 50 sats per prompt, +10 sats for each additional prompt

**File upload:** *no file upload*

 ---

### Deep Research 🌎📚🔭

⚠️ DO NOT IMPLEMENT YET

> 150 sats per prompt, 200 sats per additional prompt

**File upload:** *no file upload*

---

### Socratic Coach ☕️🧠💭

⚠️ DO NOT IMPLEMENT YET

> 50 sats per prompt, unable to prompt again

**File upload:** *images only*

---

### TLDR Summarizer 📖🤨❓

⚠️ DO NOT IMPLEMENT YET

> 150 sats per prompt, 200 sats per additional prompt

**File upload:** *PDF, epub, mobi*

---

### NSFW 🙉🙈🙊

This agent is able to answer questions and engage in behaviour that most companies try to "train out" of their agent.  No thread history is saved and all chats are lost once the user navigates away.

⚠️ DO NOT IMPLEMENT YET

> 70 sats per prompt, 20 sats per additional prompt

**File upload:** *no file upload*
