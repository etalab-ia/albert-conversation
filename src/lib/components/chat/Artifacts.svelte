<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	const i18n = getContext<Writable<i18nType>>('i18n');
	const dispatch = createEventDispatcher();

	import { chatId, settings, showArtifacts, showControls, dynamicArtifacts, forceSelectDynamicArtifacts, dynamicArtifactsHidden, theme } from '$lib/stores';
	import XMark from '../icons/XMark.svelte';
	import { copyToClipboard, createMessagesList } from '$lib/utils';
	import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import SvgPanZoom from '../common/SVGPanZoom.svelte';
	import ArrowLeft from '../icons/ArrowLeft.svelte';
	import { clearDynamicArtifacts } from '$lib/utils/artifacts';
	import MarkdownTokens from '$lib/components/chat/Messages/Markdown/MarkdownTokens.svelte';
	import Markdown from '$lib/components/chat/Messages/Markdown.svelte';
	import { marked } from 'marked';

	export let overlay = false;
	export let history;

	// Strongly-typed message structure for parsing artifacts
	type ChatMessage = { role?: string; content?: string; timestamp?: number };
	let messages: ChatMessage[] = [];

	let contents: Array<{ type: string; content: string; id?: string; title?: string; isDynamic?: boolean }> = [];
	let selectedContentIdx = 0;

	let copied = false;
	let iframeElement: HTMLIFrameElement;

	// Compute sandbox attribute string to avoid TS complaints on Settings type
	let iframeSandbox = 'allow-scripts';
	$: iframeSandbox = `allow-scripts${(($settings as any)?.iframeSandboxAllowForms ?? false) ? ' allow-forms' : ''}${(($settings as any)?.iframeSandboxAllowSameOrigin ?? false) ? ' allow-same-origin' : ''}`;

	// Theme-aware rendering for iframe contents
	let effectiveTheme: 'light' | 'dark' = 'light';
	$: {
		const currentTheme = $theme;
		if (currentTheme === 'system') {
			const prefersDark = typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
			effectiveTheme = prefersDark ? 'dark' : 'light';
		} else if (currentTheme === 'dark' || currentTheme === 'oled-dark') {
			effectiveTheme = 'dark';
		} else {
			effectiveTheme = 'light';
		}
	}

	// Re-render contents when theme changes so iframe srcdoc colors update
	$: $theme, getContents();

	// Helper to wrap arbitrary HTML with theme-aware styles for iframe srcdoc
	const buildThemedHtml = (innerHtml: string, extraCss = '', extraJs = ''): string => {
		return `
			<!DOCTYPE html>
			<html lang="en" theme="${effectiveTheme}" data-theme="${effectiveTheme}">
			<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<meta name="color-scheme" content="${effectiveTheme}">
				<${''}style>
					html, body { margin: 0; }
					:root { color-scheme: light dark; }
					html[theme='light'], html[data-theme='light'] { --bg: #ffffff; --fg: #111827; --card:#ffffff; --surface:#f9fafb; --border:#e5e7eb; --accent:#3b82f6; }
					html[theme='dark'], html[data-theme='dark'] { --bg: #161616; --fg: #e5e5e5; --card:#111827; --surface:#0f172a; --border:#374151; --accent:#3b82f6; }
					body { background-color: var(--bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
					.notification-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
					.title { font-weight: 700; margin-bottom: 14px; font-size: 16px; }
					.sources-container { display: flex; flex-direction: column; gap: 12px; }
					.source-item { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
					.source-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
					.source-number { background: var(--accent); color: white; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
					.source-content { font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
					a { color: var(--accent); text-decoration: underline; }
					${extraCss}
				</${''}style>
			</head>
			<body>
				${innerHtml}
				<${''}script>
					${extraJs}
				</${''}script>
			</body>
			</html>
		`;
	};

	const getTypeLabel = (type: string) => {
		switch (type) {
			case 'iframe':
				return $i18n.t('Notebook');
			case 'svg':
				return $i18n.t('SVG');
			case 'text':
				return $i18n.t('Text');
			case 'image':
				return $i18n.t('Image');
			case 'file':
				return $i18n.t('File');
			default:
				return type;
		}
	};

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

	// Réactivité pour l'historique des messages (toujours, même si des artefacts dynamiques existent)
	$: if (history) {
		messages = createMessagesList(history, history.currentId);
		getContents();
	}

	const getContents = () => {
		console.log('=== GET CONTENTS CALLED ===');
		console.log('Messages count:', messages.length);
		console.log('Dynamic artifacts count:', $dynamicArtifacts.length);
		
		contents = [];
		
		// 1. Extraire toujours les artefacts des messages et préparer un tableau avec horodatage pour tri stable
		let lastNormalIndex: number = -1;
		let staged: Array<{ type: string; content: string; id?: string; title?: string; isDynamic?: boolean; createdAt: number; order: number }> = [];
		let orderCounter = 0;
		messages.forEach((message) => {
			if (message?.role !== 'user' && message?.content) {
				const codeBlockContents = message.content.match(/```[\s\S]*?```/g);
				type CodeBlock = { lang: string; code: string };
				let codeBlocks: CodeBlock[] = [];

				if (codeBlockContents) {
					codeBlockContents.forEach((block: string) => {
						const lang = block.split('\n')[0].replace('```', '').trim().toLowerCase();
						const code = block.replace(/```[\s\S]*?\n/, '').replace(/```$/, '');
						codeBlocks.push({ lang, code });
					});
				}

				let htmlContent = '';
				let cssContent = '';
				let jsContent = '';

				codeBlocks.forEach((block: { lang: string; code: string }) => {
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
					inlineHtml.forEach((block: string) => {
						const content = block.replace(/<\/?html>/gi, ''); // Remove <html> tags
						htmlContent += content + '\n';
					});
				}
				if (inlineCss) {
					inlineCss.forEach((block: string) => {
						const content = block.replace(/<\/?style>/gi, ''); // Remove <style> tags
						cssContent += content + '\n';
					});
				}
				if (inlineJs) {
					inlineJs.forEach((block: string) => {
						const content = block.replace(/<\/?script>/gi, ''); // Remove <script> tags
						jsContent += content + '\n';
					});
				}

				if (htmlContent || cssContent || jsContent) {
					const renderedContent = `
						<!DOCTYPE html>
						<html lang="en" theme="${effectiveTheme}" data-theme="${effectiveTheme}">
						<head>
							<meta charset="UTF-8">
							<meta name="viewport" content="width=device-width, initial-scale=1.0">
							<meta name="color-scheme" content="${effectiveTheme}">
							<${''}style>
								html, body { margin: 0; }
								/* Base host styles driven by theme */
								:root { color-scheme: light dark; }
								html[theme='light'], html[data-theme='light'] { --bg: #ffffff; --fg: #111827; --card:#ffffff; --surface:#f9fafb; --border:#e5e7eb; --accent:#3b82f6; }
								html[theme='dark'], html[data-theme='dark'] { --bg: #161616; --fg: #e5e5e5; --card:#111827; --surface:#0f172a; --border:#374151; --accent:#3b82f6; }
								body { background-color: var(--bg); color: var(--fg); }
								.notification-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }
								.title { font-weight: 600; margin-bottom: 12px; }
								.sources-container { display: flex; flex-direction: column; gap: 12px; }
								.source-item { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
								.source-number { background: var(--accent); color: white; padding: 2px 8px; border-radius: 9999px; font-size: 12px; }

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
					staged.push({
						type: 'iframe',
						content: renderedContent,
						isDynamic: false,
						createdAt: (message?.timestamp ? message.timestamp * 1000 : Date.now()),
						order: orderCounter++
					});
					lastNormalIndex = staged.length - 1;
				} else {
					// Check for SVG content
					for (const block of codeBlocks) {
						if (block.lang === 'svg' || (block.lang === 'xml' && block.code.includes('<svg'))) {
							staged.push({
								type: 'svg',
								content: block.code,
								isDynamic: false,
								createdAt: (message?.timestamp ? message.timestamp * 1000 : Date.now()),
								order: orderCounter++
							});
							lastNormalIndex = staged.length - 1;
						}
					}
				}
			}
		});

		// 2. Ajouter les artefacts dynamiques (en conservant l'ordre d'apparition chronologique)
		console.log('Adding dynamic artifacts to staged list...');
		if (!($dynamicArtifactsHidden)) {
			$dynamicArtifacts.forEach(artifact => {
				const isFullDoc = /<!DOCTYPE html>|<html[\s>]/i.test(artifact.content);
				const looksLikeHtmlFragment = /<\w+[\s\S]*>/i.test(artifact.content);
				let contentWrapped = artifact.content;
				let coercedType = artifact.type;

				                if (artifact.type === 'iframe') {
                    // If pipeline returned our sources HTML shell, extract and format the markdown text
                    if (/<div class=\"source-content\">/i.test(artifact.content)) {
                        const matches = Array.from(artifact.content.matchAll(/<div class=\"source-content\">([\s\S]*?)<\/div>/gi));
                        const parts = matches.map((m, index) => {
                            let content = m[1]
                                .replace(/<[^>]+>/g, '')
                                .replace(/&lt;/g, '<')
                                .replace(/&gt;/g, '>')
                                .replace(/&amp;/g, '&')
                                .trim();
                            
                            // Format as markdown with proper source card structure
                            return `## Source ${index + 1}\n\n${content}`;
                        });
                        contentWrapped = parts.join('\n\n---\n\n');
                        coercedType = 'text';
                    } else if (!isFullDoc && looksLikeHtmlFragment) {
                        contentWrapped = buildThemedHtml(artifact.content);
                        coercedType = 'iframe';
                    } else if (!isFullDoc && !looksLikeHtmlFragment) {
                        // Treat as Markdown/plain text → render via Markdown renderer outside of iframe
                        contentWrapped = artifact.content ?? '';
                        coercedType = 'text';
                    }
                }
				staged.push({
					type: coercedType,
					content: contentWrapped,
					id: artifact.id,
					title: artifact.title,
					isDynamic: true,
					createdAt: artifact.timestamp ?? Date.now(),
					order: orderCounter++
				});
			});
		}

		// 3. Trier par createdAt puis par ordre d'insertion pour stabilité
		staged.sort((a, b) => (a.createdAt - b.createdAt) || (a.order - b.order));
		contents = staged.map(({ createdAt, order, ...rest }) => rest);

		console.log('Final contents array:', contents);
		console.log('Contents length:', contents.length);

		if (contents.length === 0) {
			console.log('No contents, hiding artifacts');
			showControls.set(false);
			showArtifacts.set(false);
		} else {
			console.log('Contents found, showing artifacts');
			showArtifacts.set(true);
			showControls.set(true);
		}

		// Sélectionner en priorité le dernier artefact normal (HTML/SVG), sauf si on force la sélection d'un dynamique
		if (!($forceSelectDynamicArtifacts)) {
			// dernier non dynamique
			let idx = -1;
			for (let i = contents.length - 1; i >= 0; i--) {
				if (!contents[i].isDynamic) { idx = i; break; }
			}
			selectedContentIdx = idx >= 0 ? idx : (contents.length ? contents.length - 1 : 0);
		} else if ($dynamicArtifacts.length > 0) {
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
		const cw = iframeElement?.contentWindow;
		if (!cw) return;

		// Sync app theme into iframe via attribute to allow CSS overrides inside srcdoc
		try {
			const root = cw.document?.documentElement;
			if (root) {
				root.setAttribute('data-theme', effectiveTheme);
				root.setAttribute('theme', effectiveTheme);
				// Ensure our inline <style> rules take effect: force a reflow
				const s = cw.document.createElement('style');
				s.textContent = '';
				cw.document.head.appendChild(s);
				cw.document.head.removeChild(s);
			}
		} catch (e) {
			// no-op
		}
		cw.addEventListener(
			'click',
			function (e: MouseEvent) {
				const target = (e.target as HTMLElement | null)?.closest?.('a') as HTMLAnchorElement | null;
				if (target && target.href) {
					e.preventDefault();
					const url = new URL(target.href, iframeElement.baseURI);
					if (url.origin === window.location.origin) {
						cw.history.pushState(
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
		cw.addEventListener('mouseenter', function (e: Event) {
			(e as any)?.preventDefault?.();
			cw.addEventListener('dragstart', (event: Event) => {
				(event as any)?.preventDefault?.();
			});
		});
	};

	const showFullScreen = () => {
		try {
			if (iframeElement?.requestFullscreen) {
				iframeElement.requestFullscreen();
			} else if ((iframeElement as any)?.webkitRequestFullscreen) {
				(iframeElement as any).webkitRequestFullscreen();
			} else if ((iframeElement as any)?.msRequestFullscreen) {
				(iframeElement as any).msRequestFullscreen();
			} else {
				console.warn('Fullscreen API not available');
			}
		} catch (e) {
			console.error('Fullscreen request failed', e);
		}
	};

	const closeHandler = () => {
		dispatch('close');
		// Si des artefacts dynamiques existent, les masquer pour permettre un éventuel "Reopen"
		if ($dynamicArtifacts.length > 0) {
			dynamicArtifactsHidden.set(true);
		}
		showControls.set(false);
		showArtifacts.set(false);
	};

	const closeDynamicArtifacts = () => {
		// Ne pas supprimer, simplement masquer les artefacts dynamiques
		dynamicArtifactsHidden.set(true);
		// Recalculer les contenus des messages après avoir masqué les artifacts dynamiques
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

<div class=" w-full h-full relative flex flex-col bg-gray-50 dark:bg-gray-850 p-4 rounded-l-lg border-l border-gray-200 dark:border-gray-700">
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
						{contents[selectedContentIdx].title || `${getTypeLabel(contents[selectedContentIdx].type)} ${selectedContentIdx + 1}/${contents.length}`}
						{#if contents[selectedContentIdx].isDynamic}
							<span class="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
								{$i18n.t('Sources')}
							</span>
						{:else}
							<span class="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
								{$i18n.t('Code')}
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
					<button
						class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
						on:click={closeHandler}
						title={$i18n.t('Close artifacts')}
					>
						{$i18n.t('Close')}
					</button>
					
					<button
						class="copy-code-button bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
						on:click={async () => {
							const ok = await copyToClipboard(contents[selectedContentIdx].content);
							copied = ok;
							if (ok) {
								toast.success($i18n.t('Copied'));
							} else {
								toast.error($i18n.t('Failed to copy'));
							}

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

		<div class="flex-1 w-full h-full">
			<div class=" h-full flex flex-col">
				{#if contents.length > 0}
					<div class="max-w-full w-full h-full relative">
						{#if contents[selectedContentIdx].type === 'iframe'}
							<iframe
								bind:this={iframeElement}
								title="Content"
								srcdoc={contents[selectedContentIdx].content}
								class="w-full border-0 h-full rounded-none"
								allowfullscreen
								allow="fullscreen"
								sandbox={iframeSandbox}
								on:load={iframeLoadHandler}
							></iframe>
							{#if overlay}
								<div class="absolute inset-0 z-10"></div>
							{/if}
						{:else if contents[selectedContentIdx].type === 'svg'}
							<SvgPanZoom
								className=" w-full h-full max-h-full overflow-hidden"
								svg={contents[selectedContentIdx].content}
							/>
						{:else if contents[selectedContentIdx].type === 'text'}
							<div class="w-full h-full p-4 overflow-auto text-sm">
								<Markdown id={`artifact-md-${selectedContentIdx}`} content={contents[selectedContentIdx].content} />
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
