<script lang="ts">
	import { Cyphertap, cyphertap } from 'cyphertap';

	const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	// State
	let isLoading = $state(false);
	let stats = $state<{
		balance: number;
		unit: string;
		mint_url: string;
		keyset_count: number;
		proof_count: number;
		initialized: boolean;
	} | null>(null);
	let error = $state<string | null>(null);
	let authStatus = $state<{ authenticated: boolean; isAdmin: boolean; npub: string | null }>({
		authenticated: false,
		isAdmin: false,
		npub: null
	});
	let withdrawAmount = $state(100);
	let withdrawMemo = $state('');
	let withdrawnToken = $state<string | null>(null);
	let sweptToken = $state<string | null>(null);
	let copied = $state(false);

	// Create NIP-98 auth header
	async function createAuthHeader(url: string, method: string, body?: string): Promise<string> {
		const timestamp = Math.floor(Date.now() / 1000);
		const tags: string[][] = [['u', url], ['method', method]];
		
		if (body) {
			const encoder = new TextEncoder();
			const data = encoder.encode(body);
			const hashBuffer = await crypto.subtle.digest('SHA-256', data);
			const hashArray = Array.from(new Uint8Array(hashBuffer));
			const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
			tags.push(['payload', hashHex]);
		}
		
		const event = await cyphertap.signEvent({
			kind: 27235,
			created_at: timestamp,
			tags,
			content: ''
		});
		
		const signedEvent = {
			id: event.id,
			pubkey: event.pubkey,
			created_at: timestamp,
			kind: 27235,
			tags,
			content: '',
			sig: event.signature
		};
		
		return `Nostr ${btoa(JSON.stringify(signedEvent))}`;
	}

	async function checkAuth() {
		if (!cyphertap.isLoggedIn) {
			authStatus = { authenticated: false, isAdmin: false, npub: null };
			return;
		}
		try {
			const url = `${API_URL}/api/admin/auth/info`;
			const response = await fetch(url, {
				headers: { 'Authorization': await createAuthHeader(url, 'GET') }
			});
			if (response.ok) {
				const data = await response.json();
				authStatus = { authenticated: data.authenticated, isAdmin: data.is_admin, npub: data.npub };
			}
		} catch (e) {
			console.error('Auth check failed:', e);
		}
	}

	async function fetchStats() {
		if (!authStatus.isAdmin) return;
		isLoading = true;
		error = null;
		try {
			const url = `${API_URL}/api/admin/stats`;
			const response = await fetch(url, {
				headers: { 'Authorization': await createAuthHeader(url, 'GET') }
			});
			if (!response.ok) throw new Error((await response.json()).detail || 'Failed to fetch stats');
			stats = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			isLoading = false;
		}
	}

	async function withdraw() {
		if (!authStatus.isAdmin) return;
		isLoading = true;
		error = null;
		withdrawnToken = null;
		try {
			const url = `${API_URL}/api/admin/withdraw`;
			const body = JSON.stringify({ amount: withdrawAmount, memo: withdrawMemo || undefined });
			const response = await fetch(url, {
				method: 'POST',
				headers: { 'Authorization': await createAuthHeader(url, 'POST', body), 'Content-Type': 'application/json' },
				body
			});
			const data = await response.json();
			if (!data.success) throw new Error(data.error || 'Withdrawal failed');
			withdrawnToken = data.token;
			await fetchStats();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			isLoading = false;
		}
	}

	async function sweep() {
		if (!authStatus.isAdmin) return;
		isLoading = true;
		error = null;
		sweptToken = null;
		try {
			const url = `${API_URL}/api/admin/sweep`;
			const response = await fetch(url, {
				method: 'POST',
				headers: { 'Authorization': await createAuthHeader(url, 'POST') }
			});
			const data = await response.json();
			if (!data.success) throw new Error(data.error || 'Sweep failed');
			sweptToken = data.token;
			await fetchStats();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			isLoading = false;
		}
	}

	async function copyToken(token: string) {
		await navigator.clipboard.writeText(token);
		copied = true;
		setTimeout(() => copied = false, 2000);
	}

	$effect(() => {
		if (cyphertap.isLoggedIn) checkAuth();
		else { authStatus = { authenticated: false, isAdmin: false, npub: null }; stats = null; }
	});

	$effect(() => {
		if (authStatus.isAdmin) fetchStats();
	});
</script>

<svelte:head>
	<title>Admin | PlebChat</title>
</svelte:head>

<div class="container">
	<header>
		<h1>⚡ PlebChat Admin</h1>
		<Cyphertap />
	</header>

	<main>
		{#if !cyphertap.isLoggedIn}
			<div class="card center">
				<h2>🔐 Authentication Required</h2>
				<p>Sign in with your Nostr account to access the admin panel.</p>
				<p class="muted">Only whitelisted admin npubs can access these features.</p>
			</div>
		{:else if !authStatus.isAdmin}
			<div class="card center">
				<h2>⚠️ Access Denied</h2>
				<p>Your account does not have admin privileges.</p>
				{#if authStatus.npub}
					<code>{authStatus.npub}</code>
				{/if}
			</div>
		{:else}
			<!-- Stats -->
			<div class="card">
				<div class="card-header">
					<h2>📊 Wallet Stats</h2>
					<button onclick={fetchStats} disabled={isLoading}>{isLoading ? '...' : '↻'}</button>
				</div>
				{#if stats}
					<div class="stats-grid">
						<div class="stat">
							<span class="label">Balance</span>
							<span class="value highlight">{stats.balance.toLocaleString()} {stats.unit}</span>
						</div>
						<div class="stat">
							<span class="label">Proofs</span>
							<span class="value">{stats.proof_count}</span>
						</div>
						<div class="stat">
							<span class="label">Keysets</span>
							<span class="value">{stats.keyset_count}</span>
						</div>
						<div class="stat">
							<span class="label">Status</span>
							<span class="value {stats.initialized ? 'ok' : 'err'}">{stats.initialized ? 'Connected' : 'Disconnected'}</span>
						</div>
					</div>
					<p class="muted">Mint: <code>{stats.mint_url}</code></p>
				{:else if isLoading}
					<p>Loading...</p>
				{/if}
			</div>

			<!-- Withdraw -->
			<div class="card">
				<h2>💸 Withdraw</h2>
				<div class="form-row">
					<label>
						Amount (sats)
						<input type="number" bind:value={withdrawAmount} min="1" max={stats?.balance || 0} />
					</label>
					<label>
						Memo
						<input type="text" bind:value={withdrawMemo} placeholder="optional" />
					</label>
				</div>
				<button class="primary" onclick={withdraw} disabled={isLoading || !stats || withdrawAmount > stats.balance}>
					{isLoading ? 'Generating...' : 'Generate Token'}
				</button>
				{#if withdrawnToken}
					<div class="token-box">
						<span class="ok">✓ Token Generated</span>
						<button onclick={() => copyToken(withdrawnToken!)}>{copied ? '✓ Copied' : 'Copy'}</button>
						<code class="token">{withdrawnToken}</code>
					</div>
				{/if}
			</div>

			<!-- Sweep -->
			<div class="card">
				<h2>🧹 Sweep All</h2>
				<p class="muted">Generate a single token with all funds ({stats?.balance.toLocaleString() || 0} sats)</p>
				<button class="warning" onclick={sweep} disabled={isLoading || !stats || stats.balance <= 0}>
					{isLoading ? 'Sweeping...' : 'Sweep All Funds'}
				</button>
				{#if sweptToken}
					<div class="token-box">
						<span class="ok">✓ Sweep Complete</span>
						<button onclick={() => copyToken(sweptToken!)}>{copied ? '✓ Copied' : 'Copy'}</button>
						<code class="token">{sweptToken}</code>
					</div>
				{/if}
			</div>

			<!-- Error -->
			{#if error}
				<div class="card error">
					<p>❌ {error}</p>
				</div>
			{/if}
		{/if}
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: system-ui, -apple-system, sans-serif;
		background: #1a1a2e;
		color: #eee;
	}
	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 20px;
	}
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20px 0;
		border-bottom: 1px solid #333;
		margin-bottom: 20px;
	}
	h1 { margin: 0; font-size: 1.5rem; }
	h2 { margin: 0 0 15px 0; font-size: 1.2rem; }
	.card {
		background: #252540;
		border: 1px solid #333;
		border-radius: 8px;
		padding: 20px;
		margin-bottom: 20px;
	}
	.card.center { text-align: center; padding: 40px; }
	.card.error { background: #402020; border-color: #633; }
	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
	}
	.card-header h2 { margin: 0; }
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 15px;
		margin-bottom: 15px;
	}
	.stat {
		background: #1a1a2e;
		padding: 15px;
		border-radius: 6px;
	}
	.stat .label { display: block; font-size: 0.85rem; color: #888; }
	.stat .value { display: block; font-size: 1.4rem; font-weight: bold; margin-top: 5px; }
	.stat .value.highlight { color: #0ff; }
	.stat .value.ok { color: #0f0; }
	.stat .value.err { color: #f44; }
	.muted { color: #888; font-size: 0.9rem; }
	code {
		background: #1a1a2e;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 0.85rem;
	}
	.form-row {
		display: flex;
		gap: 15px;
		margin-bottom: 15px;
	}
	.form-row label { flex: 1; }
	label { display: block; font-size: 0.9rem; color: #aaa; }
	input {
		width: 100%;
		padding: 10px;
		margin-top: 5px;
		background: #1a1a2e;
		border: 1px solid #444;
		border-radius: 6px;
		color: #eee;
		font-size: 1rem;
		box-sizing: border-box;
	}
	input:focus { outline: none; border-color: #0ff; }
	button {
		padding: 10px 20px;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		background: #333;
		color: #eee;
	}
	button:hover { background: #444; }
	button:disabled { opacity: 0.5; cursor: not-allowed; }
	button.primary { background: #0aa; color: #000; }
	button.primary:hover { background: #0cc; }
	button.warning { background: #a80; color: #000; }
	button.warning:hover { background: #ca0; }
	.token-box {
		margin-top: 15px;
		padding: 15px;
		background: #1a1a2e;
		border-radius: 6px;
	}
	.token-box .ok { color: #0f0; font-weight: bold; }
	.token-box button { float: right; padding: 5px 10px; font-size: 0.85rem; }
	.token {
		display: block;
		margin-top: 10px;
		word-break: break-all;
		font-size: 0.75rem;
		color: #888;
	}
</style>
