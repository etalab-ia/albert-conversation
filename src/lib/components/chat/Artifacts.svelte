<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { chatId, settings, showArtifacts, showControls, dynamicArtifacts, forceSelectDynamicArtifacts, dynamicArtifactsHidden } from '$lib/stores';
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

	// Styles pour les thèmes light et dark - utilisant les couleurs Tailwind
	const LIGHT_THEME_STYLE = `    <style>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 24px;
    background: linear-gradient(135deg, #f9f9f9 0%, #ececec 50%, #e3e3e3 100%);
    background-attachment: fixed;
    min-height: 100vh;
    box-sizing: border-box;
}

.notification-card {
    background: rgba(249, 249, 249, 0.98);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.04);
    width: 90%;
    max-width: 90%;
    color: #333;
    animation: fadeInUp 0.6s ease-out;
    height: 95%;
    border: 1px solid #e3e3e3;
}

.title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 24px;
    text-align: center;
    color: #161616;
    letter-spacing: -0.02em;
}

.content {
    font-size: 16px;
    line-height: 1.7;
    text-align: justify;
    color: #4e4e4e;
}

.highlight {
    background: linear-gradient(120deg, #e3e3e3 0%, #cdcdcd 100%);
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    color: #161616;
}

.sources-container {
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 95%;
    overflow-y: auto;
    padding-right: 8px;
	padding-left: 8px;
    padding-bottom: 0px;
}

.source-item {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05), 0 1px 4px rgba(0, 0, 0, 0.03);
    border: 1px solid #e3e3e3;
    animation: fadeInUp 0.6s ease-out both;
    position: relative;
    overflow: visible;
    width: 100%;
    box-sizing: border-box;
    min-height: auto;
    height: auto;
}

.source-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 2%;
    right: 2%;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    transform: scaleX(0);
    transition: transform 0.3s ease;
	border-radius: 32px;
}

.source-item:hover::before {
    transform: scaleX(1);
}

.source-item:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.06);
    transform: translateY(-2px);
    border-color: #cdcdcd;
}

.source-header {
    display: flex;
    margin-bottom: 16px;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    width: 100%;
}

.source-number {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
    white-space: nowrap;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    letter-spacing: 0.5px;
}

.source-link {
    color: #676767;
    text-decoration: none;
    transition: all 0.2s ease;
    font-weight: 500;
}

.source-link:hover {
    color: #3b82f6;
    text-decoration: underline;
}

.source-title {
    color: #161616;
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 12px;
    line-height: 1.4;
    display: block;
    width: 100%;
}

.source-content {
    font-size: 14px;
    line-height: 1.6;
    color: #4e4e4e;
    background: linear-gradient(135deg, #f9f9f9 0%, #ececec 100%);
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #3b82f6;
    word-wrap: break-word;
    word-break: break-word;
    overflow-wrap: break-word;
    position: relative;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
    width: 100%;
    box-sizing: border-box;
    display: block;
    min-height: 40px;
    overflow: visible;
}

/* Animation d'entrée améliorée */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(32px) scale(0.96);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Délais d'animation échelonnés pour les sources */
.source-item:nth-child(1) { animation-delay: 0.1s; }
.source-item:nth-child(2) { animation-delay: 0.15s; }
.source-item:nth-child(3) { animation-delay: 0.2s; }
.source-item:nth-child(4) { animation-delay: 0.25s; }
.source-item:nth-child(5) { animation-delay: 0.3s; }
.source-item:nth-child(6) { animation-delay: 0.35s; }
.source-item:nth-child(7) { animation-delay: 0.4s; }
.source-item:nth-child(8) { animation-delay: 0.45s; }

/* Scrollbar améliorée */
.sources-container::-webkit-scrollbar {
    width: 8px;
}

.sources-container::-webkit-scrollbar-track {
    background: #ececec;
    border-radius: 8px;
}

.sources-container::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #cdcdcd 0%, #b4b4b4 100%);
    border-radius: 8px;
    border: 2px solid #ececec;
}

.sources-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #b4b4b4 0%, #9b9b9b 100%);
}

/* Responsive amélioré */
@media (max-width: 768px) {
    body {
        padding: 16px;
    }
    
    .notification-card {
        padding: 20px;
        border-radius: 12px;
    }
    
    .title {
        font-size: 24px;
        margin-bottom: 20px;
    }
    
    .source-item {
        padding: 20px;
    }
    
    .source-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
    
    .sources-container {
        gap: 16px;
    }
}

/* Optionnel: animation au scroll pour les éléments qui apparaissent plus tard */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
    </style>`;

	const DARK_THEME_STYLE = `    <style>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 24px;
    background: linear-gradient(135deg, #0d0d0d 0%, #161616 50%, #262626 100%);
    background-attachment: fixed;
    min-height: 100vh;
    box-sizing: border-box;
}

.notification-card {
    background: rgba(22, 22, 22, 0.98);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.2);
    width: 90%;
    max-width: 90%;
    color: #f9f9f9;
    animation: fadeInUp 0.6s ease-out;
    height: 95%;
    border: 1px solid #333;
    backdrop-filter: blur(8px);
}

.title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 24px;
    text-align: center;
    color: #f9f9f9;
    letter-spacing: -0.02em;
}

.content {
    font-size: 16px;
    line-height: 1.7;
    text-align: justify;
    color: #9b9b9b;
}

.highlight {
    background: linear-gradient(120deg, #4e4e4e 0%, #676767 100%);
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    color: #f9f9f9;
    box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.1);
}

.sources-container {
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 95%;
    overflow-y: auto;
    padding-right: 8px;
	padding-left: 8px;
    padding-bottom: 0px;
}

.source-item {
    background: rgba(51, 51, 51, 0.9);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 1px 4px rgba(0, 0, 0, 0.15);
    border: 1px solid #4e4e4e;
    animation: fadeInUp 0.6s ease-out both;
    position: relative;
    overflow: visible;
    backdrop-filter: blur(4px);
    width: 100%;
    box-sizing: border-box;
    min-height: auto;
    height: auto;
}


.source-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 2%;
    right: 2%;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
    transform: scaleX(0);
    transition: transform 0.3s ease;
	border-radius: 32px;
}

.source-item:hover::before {
    transform: scaleX(1);
}

.source-item:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.25);
    transform: translateY(-2px);
    border-color: #676767;
    background: rgba(78, 78, 78, 0.9);
}

.source-header {
    display: flex;
    margin-bottom: 16px;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    width: 100%;
}

.source-number {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
    white-space: nowrap;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    letter-spacing: 0.5px;
}

.source-link {
    color: #9b9b9b;
    text-decoration: none;
    transition: all 0.2s ease;
    font-weight: 500;
}

.source-link:hover {
    color: #60a5fa;
    text-decoration: underline;
}

.source-title {
    color: #f9f9f9;
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 12px;
    line-height: 1.4;
    display: block;
    width: 100%;
}

.source-content {
    font-size: 14px;
    line-height: 1.6;
    color: #cdcdcd;
    background: linear-gradient(135deg, #262626 0%, #161616 100%);
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #3b82f6;
    word-wrap: break-word;
    word-break: break-word;
    overflow-wrap: break-word;
    position: relative;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
    width: 100%;
    box-sizing: border-box;
}

/* Animation d'entrée améliorée */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(32px) scale(0.96);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Délais d'animation échelonnés pour les sources */
.source-item:nth-child(1) { animation-delay: 0.1s; }
.source-item:nth-child(2) { animation-delay: 0.15s; }
.source-item:nth-child(3) { animation-delay: 0.2s; }
.source-item:nth-child(4) { animation-delay: 0.25s; }
.source-item:nth-child(5) { animation-delay: 0.3s; }
.source-item:nth-child(6) { animation-delay: 0.35s; }
.source-item:nth-child(7) { animation-delay: 0.4s; }
.source-item:nth-child(8) { animation-delay: 0.45s; }

/* Scrollbar améliorée */
.sources-container::-webkit-scrollbar {
    width: 8px;
}

.sources-container::-webkit-scrollbar-track {
    background: #333;
    border-radius: 8px;
}

.sources-container::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #676767 0%, #4e4e4e 100%);
    border-radius: 8px;
    border: 2px solid #333;
}

.sources-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #9b9b9b 0%, #676767 100%);
}

/* Responsive amélioré */
@media (max-width: 768px) {
    body {
        padding: 16px;
    }
    
    .notification-card {
        padding: 20px;
        border-radius: 12px;
    }
    
    .title {
        font-size: 24px;
        margin-bottom: 20px;
    }
    
    .source-item {
        padding: 20px;
    }
    
    .source-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
    
    .sources-container {
        gap: 16px;
    }
}

/* Optionnel: animation au scroll pour les éléments qui apparaissent plus tard */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
    </style>`;

	// Variable réactive pour le contenu de l'iframe avec le bon thème
	let themedSrcdoc: string;

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

	// Réactivité pour l'injection du thème dans les artefacts dynamiques de type iframe
	$: if (contents.length > 0 && contents[selectedContentIdx]) {
		const currentContent = contents[selectedContentIdx];
		if (currentContent.isDynamic && currentContent.type === 'iframe' && currentContent.content.includes('{{THEME_STYLE}}')) {
			// Détecter le thème actuel
			const isDark = typeof document !== 'undefined' && 
				(document.documentElement.getAttribute('theme') === 'dark' || 
				 document.documentElement.classList.contains('dark'));
			
			// Choisir le style approprié
			const themeStyle = isDark ? DARK_THEME_STYLE : LIGHT_THEME_STYLE;
			
			// Remplacer le placeholder par le style thématisé
			themedSrcdoc = currentContent.content.replace('{{THEME_STYLE}}', themeStyle);
		} else {
			// Pour les autres types d'artefacts, utiliser le contenu tel quel
			themedSrcdoc = currentContent.content;
		}
	} else {
		themedSrcdoc = '';
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
				staged.push({
					type: artifact.type,
					content: artifact.content,
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
		const unsubscribeArtifacts = showArtifacts.subscribe(value => {
			console.log('=== SHOW ARTIFACTS CHANGED ===');
			console.log('New value:', value);
			console.log('=== END SHOW ARTIFACTS LOG ===');
		});

		// Observer les changements de thème pour mettre à jour l'iframe
		const themeObserver = new MutationObserver((mutations) => {
			mutations.forEach((mutation) => {
				if (mutation.type === 'attributes' && 
					(mutation.attributeName === 'theme' || mutation.attributeName === 'class')) {
					console.log('Theme changed, triggering reactive update...');
					// Forcer la mise à jour réactive en changeant selectedContentIdx
					selectedContentIdx = selectedContentIdx;
				}
			});
		});

		// Observer les changements d'attributs sur document.documentElement
		if (typeof document !== 'undefined') {
			themeObserver.observe(document.documentElement, {
				attributes: true,
				attributeFilter: ['theme', 'class']
			});
		}
		
		return () => {
			unsubscribeArtifacts();
			themeObserver.disconnect();
		};
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
								srcdoc={themedSrcdoc}
								class="w-full border-0 h-full rounded-none"
								allowfullscreen
								allow="fullscreen"
								sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox{($settings?.iframeSandboxAllowForms ?? false)
									? ' allow-forms'
									: ''}{($settings?.iframeSandboxAllowSameOrigin ?? false)
									? ' allow-same-origin'
									: ''}"
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
