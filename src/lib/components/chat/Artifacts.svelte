<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { chatId, settings, showArtifacts, showControls, dynamicArtifacts } from '$lib/stores';
	import XMark from '../icons/XMark.svelte';
	import { copyToClipboard, createMessagesList } from '$lib/utils';
	import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import SvgPanZoom from '../common/SVGPanZoom.svelte';
	import ArrowLeft from '../icons/ArrowLeft.svelte';
	import { clearDynamicArtifacts } from '$lib/utils/artifacts';

	export let overlay = false;
	export let history;
	let messages = [];

	let contents: Array<{ type: string; content: string; id?: string; title?: string; isDynamic?: boolean }> = [];
	let selectedContentIdx = 0;

	let copied = false;
	let iframeElement: HTMLIFrameElement;

	$: if (history) {
		messages = createMessagesList(history, history.currentId);
		getContents();
	} else {
		messages = [];
		getContents();
	}

	// Réactivité pour les artefacts dynamiques
	$: if ($dynamicArtifacts.length > 0) {
		console.log('=== DYNAMIC ARTIFACTS UPDATED ===');
		console.log('Dynamic artifacts count:', $dynamicArtifacts.length);
		console.log('Dynamic artifacts:', $dynamicArtifacts);
		getContents();
	}

	// Réactivité pour l'historique des messages
	$: if (history && $dynamicArtifacts.length === 0) {
		messages = createMessagesList(history, history.currentId);
		getContents();
	}

	const getContents = () => {
		console.log('=== GET CONTENTS CALLED ===');
		console.log('Messages count:', messages.length);
		console.log('Dynamic artifacts count:', $dynamicArtifacts.length);
		
		contents = [];
		
		// 1. Extraire les artefacts des messages (seulement si pas d'artifacts dynamiques prioritaires)
		if ($dynamicArtifacts.length === 0) {
			messages.forEach((message) => {
				if (message?.role !== 'user' && message?.content) {
					const codeBlockContents = message.content.match(/```[\s\S]*?```/g);
					let codeBlocks = [];

					if (codeBlockContents) {
						codeBlockContents.forEach((block) => {
							const lang = block.split('\n')[0].replace('```', '').trim().toLowerCase();
							const code = block.replace(/```[\s\S]*?\n/, '').replace(/```$/, '');
							codeBlocks.push({ lang, code });
						});
					}

					let htmlContent = '';
					let cssContent = '';
					let jsContent = '';

					codeBlocks.forEach((block) => {
						const { lang, code } = block;

						if (lang === 'html') {
							htmlContent += code + '\n';
						} else if (lang === 'css') {
							cssContent += code + '\n';
						} else if (lang === 'javascript' || lang === 'js') {
							jsContent += code + '\n';
						}
					});

					const inlineHtml = message.content.match(/<html>[\s\S]*?<\/html>/gi);
					const inlineCss = message.content.match(/<style>[\s\S]*?<\/style>/gi);
					const inlineJs = message.content.match(/<script>[\s\S]*?<\/script>/gi);

					if (inlineHtml) {
						inlineHtml.forEach((block) => {
							const content = block.replace(/<\/?html>/gi, ''); // Remove <html> tags
							htmlContent += content + '\n';
						});
					}
					if (inlineCss) {
						inlineCss.forEach((block) => {
							const content = block.replace(/<\/?style>/gi, ''); // Remove <style> tags
							cssContent += content + '\n';
						});
					}
					if (inlineJs) {
						inlineJs.forEach((block) => {
							const content = block.replace(/<\/?script>/gi, ''); // Remove <script> tags
							jsContent += content + '\n';
						});
					}

					if (htmlContent || cssContent || jsContent) {
						const renderedContent = `
							<!DOCTYPE html>
							<html lang="en">
							<head>
								<meta charset="UTF-8">
								<meta name="viewport" content="width=device-width, initial-scale=1.0">
								<${''}style>
									body {
										background-color: white; /* Ensure the iframe has a white background */
									}

									${cssContent}
								</${''}style>
							</head>
							<body>
								${htmlContent}

								<${''}script>
									${jsContent}
								</${''}script>
							</body>
							</html>
						`;
						contents = [...contents, { type: 'iframe', content: renderedContent }];
					} else {
						// Check for SVG content
						for (const block of codeBlocks) {
							if (block.lang === 'svg' || (block.lang === 'xml' && block.code.includes('<svg'))) {
								contents = [...contents, { type: 'svg', content: block.code }];
							}
						}
					}
				}
			});
		}

		// 2. Ajouter les artefacts dynamiques (prioritaires)
		console.log('Adding dynamic artifacts to contents...');
		$dynamicArtifacts.forEach(artifact => {
			console.log('Processing dynamic artifact:', artifact);
			contents.push({
				type: artifact.type,
				content: artifact.content,
				id: artifact.id,
				title: artifact.title,
				isDynamic: true
			});
		});

		console.log('Final contents array:', contents);
		console.log('Contents length:', contents.length);

		if (contents.length === 0) {
			console.log('No contents, hiding artifacts');
			showControls.set(false);
			showArtifacts.set(false);
		} else {
			console.log('Contents found, showing artifacts');
		}

		// Si on a des artifacts dynamiques, sélectionner le plus récent
		if ($dynamicArtifacts.length > 0) {
			selectedContentIdx = contents.length - 1;
		} else {
			selectedContentIdx = contents ? contents.length - 1 : 0;
		}
		
		console.log('Selected content index:', selectedContentIdx);
		console.log('=== END GET CONTENTS ===');
	};

	function navigateContent(direction: 'prev' | 'next') {
		console.log(selectedContentIdx);

		selectedContentIdx =
			direction === 'prev'
				? Math.max(selectedContentIdx - 1, 0)
				: Math.min(selectedContentIdx + 1, contents.length - 1);

		console.log(selectedContentIdx);
	}

	const iframeLoadHandler = () => {
		iframeElement.contentWindow.addEventListener(
			'click',
			function (e) {
				const target = e.target.closest('a');
				if (target && target.href) {
					e.preventDefault();
					const url = new URL(target.href, iframeElement.baseURI);
					if (url.origin === window.location.origin) {
						iframeElement.contentWindow.history.pushState(
							null,
							'',
							url.pathname + url.search + url.hash
						);
					} else {
						console.log('External navigation blocked:', url.href);
					}
				}
			},
			true
		);

		// Cancel drag when hovering over iframe
		iframeElement.contentWindow.addEventListener('mouseenter', function (e) {
			e.preventDefault();
			iframeElement.contentWindow.addEventListener('dragstart', (event) => {
				event.preventDefault();
			});
		});
	};

	const showFullScreen = () => {
		if (iframeElement.requestFullscreen) {
			iframeElement.requestFullscreen();
		} else if (iframeElement.webkitRequestFullscreen) {
			iframeElement.webkitRequestFullscreen();
		} else if (iframeElement.msRequestFullscreen) {
			iframeElement.msRequestFullscreen();
		}
	};

	const closeHandler = () => {
		dispatch('close');
		showControls.set(false);
		showArtifacts.set(false);
		clearDynamicArtifacts();
	};

	const closeDynamicArtifacts = () => {
		clearDynamicArtifacts();
		// Recalculer les contenus des messages après avoir fermé les artifacts dynamiques
		if (history) {
			messages = createMessagesList(history, history.currentId);
			getContents();
		}
	};

	onMount(() => {
		console.log('=== ARTIFACTS COMPONENT MOUNTED ===');
		console.log('Initial dynamic artifacts count:', $dynamicArtifacts.length);
		console.log('Initial showArtifacts value:', $showArtifacts);
		console.log('=== END MOUNT ===');
		
		// Surveiller les changements de showArtifacts
		const unsubscribe = showArtifacts.subscribe(value => {
			console.log('=== SHOW ARTIFACTS CHANGED ===');
			console.log('New value:', value);
			console.log('=== END SHOW ARTIFACTS LOG ===');
		});
		
		return unsubscribe;
	});
</script>

<div class=" w-full h-full relative flex flex-col bg-gray-50 dark:bg-gray-850">
	<div class="w-full h-full flex flex-col flex-1 relative">
		{#if contents.length > 0}
			<div class="flex items-center justify-between w-full mb-4">
				<div class="flex items-center gap-2">
					<button
						class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
						on:click={() => navigateContent('prev')}
						disabled={contents.length <= 1}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
							class="size-3.5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="m15.75 19.5-7.5-7.5 7.5-7.5"
							/>
						</svg>
					</button>

					<div class="text-sm font-medium">
						{contents[selectedContentIdx].title || `${contents[selectedContentIdx].type} ${selectedContentIdx + 1}/${contents.length}`}
						{#if contents[selectedContentIdx].isDynamic}
							<span class="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
								{$i18n.t('Dynamic')}
							</span>
						{/if}
					</div>

					<button
						class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
						on:click={() => navigateContent('next')}
						disabled={contents.length <= 1}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
							class="size-3.5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="m8.25 4.5 7.5 7.5-7.5 7.5"
							/>
						</svg>
					</button>
				</div>

				<div class="flex items-center gap-1">
					{#if $dynamicArtifacts.length > 0}
						<button
							class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
							on:click={closeDynamicArtifacts}
							title={$i18n.t('Close dynamic artifacts')}
						>
							{$i18n.t('Close Dynamic')}
						</button>
					{/if}
					
					<button
						class="copy-code-button bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
						on:click={() => {
							copyToClipboard(contents[selectedContentIdx].content);
							copied = true;

							setTimeout(() => {
								copied = false;
							}, 2000);
						}}>{copied ? $i18n.t('Copied') : $i18n.t('Copy')}</button
					>

					{#if contents[selectedContentIdx].type === 'iframe'}
						<Tooltip content={$i18n.t('Open in full screen')}>
							<button
								class=" bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
								on:click={showFullScreen}
							>
								<ArrowsPointingOut className="size-3.5" />
							</button>
						</Tooltip>
					{/if}
				</div>
			</div>
		{/if}

		{#if overlay}
			<div class=" absolute top-0 left-0 right-0 bottom-0 z-10"></div>
		{/if}

		<div class="flex-1 w-full h-full">
			<div class=" h-full flex flex-col">
				{#if contents.length > 0}
					<div class="max-w-full w-full h-full">
						{#if contents[selectedContentIdx].type === 'iframe'}
							<iframe
								bind:this={iframeElement}
								title="Content"
								srcdoc={contents[selectedContentIdx].content}
								class="w-full border-0 h-full rounded-none"
								sandbox="allow-scripts{($settings?.iframeSandboxAllowForms ?? false)
									? ' allow-forms'
									: ''}{($settings?.iframeSandboxAllowSameOrigin ?? false)
									? ' allow-same-origin'
									: ''}"
								on:load={iframeLoadHandler}
							></iframe>
						{:else if contents[selectedContentIdx].type === 'svg'}
							<SvgPanZoom
								className=" w-full h-full max-h-full overflow-hidden"
								svg={contents[selectedContentIdx].content}
							/>
						{:else if contents[selectedContentIdx].type === 'text'}
							<div class="w-full h-full p-4 overflow-auto">
								<pre class="whitespace-pre-wrap text-sm font-mono text-gray-900 dark:text-white">{contents[selectedContentIdx].content}</pre>
							</div>
						{:else if contents[selectedContentIdx].type === 'image'}
							<div class="w-full h-full flex items-center justify-center p-4">
								<img 
									src={contents[selectedContentIdx].content} 
									alt={contents[selectedContentIdx].title || 'Image'} 
									class="max-w-full max-h-full object-contain"
								/>
							</div>
						{:else if contents[selectedContentIdx].type === 'file'}
							<div class="w-full h-full p-4">
								<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
									<div class="text-lg font-medium text-gray-900 dark:text-white mb-2">
										{contents[selectedContentIdx].title || 'Fichier'}
									</div>
									<div class="text-sm text-gray-500 dark:text-gray-400 mb-4">
										{contents[selectedContentIdx].content}
									</div>
									<a 
										href={contents[selectedContentIdx].content} 
										download
										class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
									>
										Télécharger
									</a>
								</div>
							</div>
						{/if}
					</div>
				{:else}
					<div class="m-auto font-medium text-xs text-gray-900 dark:text-white">
						{$i18n.t('No HTML, CSS, or JavaScript content found.')}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
