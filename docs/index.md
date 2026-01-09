# What is PlebChat?

⚠️ Coding agents must ALWAYS read [their instructions](../README.md).

---

**PlebChat** is a simple AI chat web application that demonstrates:


This repo will be a simple AI chat application:

 - The UI will be in frontend/ and made with Svelte 5
 - The included CypherTap submodule will be used to handle user login, bitcoin wallet storage and ecash payments for pay-per-use AI usage.
 - The backend/ will be Python3.12 FastAPI and will be used to validate and redeem ecash tokens to a local ecash wallet
 - The agents/ will contain LangGraph agents.  To start we'll only have ONE agent which should consist of a single LLM call.  The graph should redeem the ecash token before execution.



---






- **Nostr Protocol:**
    - **Users** are just simply public/private key pairs - no usernames/passwords. Usage of a NIP-07 browser extention elevates this experience even further.
    - **Just works** - Nostr protocol is used "under the hood" and should be largely invisible to the user. We aim for an experience that *"just works"* with only the "advanced user" suspecting usage of the nostr protocol.
    - **Decentralized Sync** — Book "announcements" and book annotations are sent via user-specified relays.
    - **No central databases** - relays > central databases

- **Client-Side Storage:**
    - **Local Browser Storage:** All application data is stored in the user's browser, you own your data.
    - Avoid "app store" ecosystem lock-in - we don't need approval to publish freedom tech apps
    - Core experience is ran on user's device.

- **eCash Payments:**
    - **Bitcoin payments:** *any human* can pay for this service to enhance their learning without risk of government "money" regulations locking them out.
    - **Pay-per-use** AI features avoid subscriptions therefore the over-charging of users who don't maximize their monthly usage.
    - **Self-custody** prevents risk of centralized theft of user funds - private keys are stored on user's devices.
