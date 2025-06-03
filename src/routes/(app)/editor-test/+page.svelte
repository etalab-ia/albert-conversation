<script lang="ts">
	import BlockNoteEditor from '$lib/components/common/BlockNoteEditor.svelte';
	import { onMount } from 'svelte';

	let markdownContent = `# Welcome to BlockNote Editor Test

This is a **test page** to verify that the BlockNote editor is working correctly.

## Features to test:
- Text editing
- **Bold text**
- *Italic text*
- Lists:
  1. Numbered items
  2. Another item
- Code blocks
- Headings

\`\`\`javascript
console.log("Hello World!");
\`\`\`

Try editing this content to see if the editor is working!`;

	let editor: BlockNoteEditor;
	let currentContent = '';

	const handleGetContent = async () => {
		if (editor) {
			currentContent = await editor.getMarkdown();
			console.log('Current content:', currentContent);
		}
	};

	onMount(() => {
		console.log('Editor test page mounted');
	});
</script>

<svelte:head>
	<title>BlockNote Editor Test</title>
</svelte:head>

<div class="flex flex-col h-screen p-6 bg-gray-50 dark:bg-gray-900">
	<div class="mb-4">
		<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
			BlockNote Editor Test
		</h1>
		<p class="text-gray-600 dark:text-gray-400">
			Test the editing capabilities of the BlockNote editor component.
		</p>
	</div>

	<div class="flex gap-4 mb-4">
		<button
			class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
			on:click={handleGetContent}
		>
			Get Content
		</button>
		<button
			class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition"
			on:click={() => {
				markdownContent = `# New Content

This is new content loaded into the editor.

**Try editing this!**`;
			}}
		>
			Load New Content
		</button>
	</div>

	<div class="flex-1 border-2 border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
		<BlockNoteEditor
			bind:this={editor}
			bind:markdownContent
			editable={true}
			className="w-full h-full"
		/>
	</div>

	{#if currentContent}
		<div class="mt-4 p-4 bg-white dark:bg-gray-800 rounded border">
			<h3 class="font-semibold mb-2 text-gray-900 dark:text-white">Current Content (Markdown):</h3>
			<pre class="text-sm bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-auto text-gray-900 dark:text-white">{currentContent}</pre>
		</div>
	{/if}
</div> 