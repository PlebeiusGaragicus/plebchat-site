<script lang="ts">
	import { marked } from 'marked';
	import hljs from 'highlight.js/lib/core';
	// Import common languages
	import javascript from 'highlight.js/lib/languages/javascript';
	import typescript from 'highlight.js/lib/languages/typescript';
	import python from 'highlight.js/lib/languages/python';
	import bash from 'highlight.js/lib/languages/bash';
	import json from 'highlight.js/lib/languages/json';
	import xml from 'highlight.js/lib/languages/xml';
	import css from 'highlight.js/lib/languages/css';
	import sql from 'highlight.js/lib/languages/sql';
	import rust from 'highlight.js/lib/languages/rust';
	import go from 'highlight.js/lib/languages/go';
	import { cn } from '$lib/utils.js';

	// Register languages
	hljs.registerLanguage('javascript', javascript);
	hljs.registerLanguage('js', javascript);
	hljs.registerLanguage('typescript', typescript);
	hljs.registerLanguage('ts', typescript);
	hljs.registerLanguage('python', python);
	hljs.registerLanguage('py', python);
	hljs.registerLanguage('bash', bash);
	hljs.registerLanguage('sh', bash);
	hljs.registerLanguage('shell', bash);
	hljs.registerLanguage('json', json);
	hljs.registerLanguage('html', xml);
	hljs.registerLanguage('xml', xml);
	hljs.registerLanguage('css', css);
	hljs.registerLanguage('sql', sql);
	hljs.registerLanguage('rust', rust);
	hljs.registerLanguage('rs', rust);
	hljs.registerLanguage('go', go);
	hljs.registerLanguage('golang', go);

	interface Props {
		content: string;
		class?: string;
	}

	let { content, class: className }: Props = $props();

	// Custom renderer for marked with syntax highlighting
	const renderer = new marked.Renderer();

	renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
		const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
		let highlighted: string;

		try {
			if (language !== 'plaintext' && hljs.getLanguage(language)) {
				highlighted = hljs.highlight(text, { language }).value;
			} else {
				highlighted = hljs.highlightAuto(text).value;
			}
		} catch {
			highlighted = text
				.replace(/&/g, '&amp;')
				.replace(/</g, '&lt;')
				.replace(/>/g, '&gt;');
		}

		const langLabel = lang || 'code';
		return `<div class="code-block-wrapper">
			<div class="code-block-header">
				<span class="code-lang">${langLabel}</span>
			</div>
			<pre><code class="hljs language-${language}">${highlighted}</code></pre>
		</div>`;
	};

	// Configure marked
	marked.setOptions({
		gfm: true,
		breaks: true
	});

	// Parse markdown to HTML with custom renderer
	let html = $derived(marked.parse(content, { renderer, async: false }) as string);
</script>

<div
	class={cn(
		'markdown-content prose prose-invert prose-sm max-w-none',
		// Headings
		'prose-headings:text-[var(--color-text-primary)] prose-headings:font-semibold',
		// Paragraphs
		'prose-p:text-[var(--color-text-primary)] prose-p:leading-relaxed prose-p:my-2',
		// Links
		'prose-a:text-[var(--color-accent-primary)] prose-a:no-underline hover:prose-a:underline',
		// Lists
		'prose-li:text-[var(--color-text-primary)] prose-li:my-0.5',
		'prose-ul:my-2 prose-ol:my-2',
		// Inline code - use natural code colors, not accent
		'prose-code:text-[var(--color-code-text)] prose-code:bg-[var(--color-bg-tertiary)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-normal prose-code:before:content-none prose-code:after:content-none prose-code:border prose-code:border-[var(--color-border-hover)]',
		// Pre/code blocks - styling handled by custom wrapper
		'prose-pre:bg-transparent prose-pre:p-0 prose-pre:border-0 prose-pre:my-0',
		// Blockquote
		'prose-blockquote:border-l-[var(--color-purple-accent)] prose-blockquote:text-[var(--color-text-secondary)] prose-blockquote:not-italic',
		// Strong/bold
		'prose-strong:text-[var(--color-text-primary)] prose-strong:font-semibold',
		// Tables
		'prose-th:text-[var(--color-text-primary)] prose-td:text-[var(--color-text-secondary)]',
		className
	)}
>
	{@html html}
</div>

<style>
	/* Code block wrapper */
	.markdown-content :global(.code-block-wrapper) {
		margin: 0.75rem 0;
		border-radius: 0.5rem;
		border: 1px solid var(--color-border-hover);
		background: var(--color-bg-tertiary);
		overflow: hidden;
	}

	/* Code block header with language label */
	.markdown-content :global(.code-block-header) {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 0.75rem;
		background: var(--color-bg-elevated);
		border-bottom: 1px solid var(--color-border-hover);
	}

	.markdown-content :global(.code-lang) {
		font-size: 0.7rem;
		font-weight: 500;
		text-transform: uppercase;
		color: var(--color-text-muted);
		font-family: var(--font-mono);
	}

	/* Pre and code block styling */
	.markdown-content :global(.code-block-wrapper pre) {
		margin: 0;
		padding: 0;
		background: transparent;
	}

	.markdown-content :global(.code-block-wrapper code) {
		display: block;
		padding: 1rem;
		overflow-x: auto;
		font-size: 0.8125rem;
		line-height: 1.6;
		background: transparent;
		border: none;
		color: var(--color-code-text);
	}

	/* Inline code should not have the block styling */
	.markdown-content :global(:not(pre) > code) {
		font-size: 0.875em;
	}

	/* ============================================
	   Syntax Highlighting Theme (Dark)
	   ============================================ */

	/* Keywords (if, else, return, function, const, let, etc.) */
	.markdown-content :global(.hljs-keyword),
	.markdown-content :global(.hljs-selector-tag),
	.markdown-content :global(.hljs-built_in),
	.markdown-content :global(.hljs-type) {
		color: #c792ea;
	}

	/* Strings */
	.markdown-content :global(.hljs-string),
	.markdown-content :global(.hljs-attr),
	.markdown-content :global(.hljs-template-variable),
	.markdown-content :global(.hljs-addition) {
		color: #c3e88d;
	}

	/* Numbers */
	.markdown-content :global(.hljs-number),
	.markdown-content :global(.hljs-literal) {
		color: #f78c6c;
	}

	/* Function names */
	.markdown-content :global(.hljs-title),
	.markdown-content :global(.hljs-section),
	.markdown-content :global(.hljs-selector-id) {
		color: #82aaff;
	}

	/* Variables and parameters */
	.markdown-content :global(.hljs-variable),
	.markdown-content :global(.hljs-params),
	.markdown-content :global(.hljs-template-tag) {
		color: #f07178;
	}

	/* Comments */
	.markdown-content :global(.hljs-comment),
	.markdown-content :global(.hljs-quote) {
		color: #676e95;
		font-style: italic;
	}

	/* Attributes (HTML/JSX) */
	.markdown-content :global(.hljs-name),
	.markdown-content :global(.hljs-attribute) {
		color: #ffcb6b;
	}

	/* Tags (HTML) */
	.markdown-content :global(.hljs-tag) {
		color: #f07178;
	}

	/* Punctuation and operators */
	.markdown-content :global(.hljs-punctuation),
	.markdown-content :global(.hljs-operator) {
		color: #89ddff;
	}

	/* Class names */
	.markdown-content :global(.hljs-class .hljs-title),
	.markdown-content :global(.hljs-title.class_) {
		color: #ffcb6b;
	}

	/* Regex */
	.markdown-content :global(.hljs-regexp) {
		color: #89ddff;
	}

	/* Meta/preprocessor */
	.markdown-content :global(.hljs-meta),
	.markdown-content :global(.hljs-meta-keyword) {
		color: #89ddff;
	}

	/* Deletion */
	.markdown-content :global(.hljs-deletion) {
		color: #f07178;
		background: rgba(240, 113, 120, 0.15);
	}

	/* Emphasis */
	.markdown-content :global(.hljs-emphasis) {
		font-style: italic;
	}

	.markdown-content :global(.hljs-strong) {
		font-weight: bold;
	}

	/* Horizontal rules */
	.markdown-content :global(hr) {
		border-color: var(--color-border-default);
		margin: 1.5rem 0;
	}

	/* Task lists */
	.markdown-content :global(input[type='checkbox']) {
		margin-right: 0.5rem;
		accent-color: var(--color-accent-primary);
	}
</style>
