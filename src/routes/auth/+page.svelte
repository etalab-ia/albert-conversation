<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { onMount, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getBackendConfig } from '$lib/apis';
	import { ldapUserSignIn, getSessionUser, userSignIn, userSignUp } from '$lib/apis/auths';

	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';
	import Header from '$lib/components/layout/Header.svelte';
	import Footer from '$lib/components/chat/Footer.svelte';
	import ProconnectButton from '$lib/components/auth/ProconnectButton.svelte';

	import { fade, fly } from 'svelte/transition';

	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');
	const _paq = window._paq;

	interface SessionUser {
		token: string;
		id: string;
		email: string;
		name: string;
		role: string;
		profile_image_url: string;
	}

	let loaded = false;
	let name = '';
	let email = '';
	let password = '';
	let onboarding = false;

	// Carousel state
	let currentIndex = 0;
	const carouselItems = [
		{
			chat1: $i18n.t('Can you summarize this document for me 📖?'),
			chat2: $i18n.t('Certainly! Here is a concise summary of the document you provided.'),
			image: '/assets/illustrations/code3.png'
		},
		{
			chat1: $i18n.t('Can you create a web form for me?'),
			chat2: $i18n.t(
				'Of course! Here is a Python function that reverses a string:\n\ndef reverse_string(s):\n    return s[::-1]'
			),
			image: '/assets/illustrations/code3.png'
		},
		{
			chat1: $i18n.t('What is the latest news about AI research?'),
			chat2: $i18n.t('Let me search the internet for the most recent updates on AI research.'),
			image: '/assets/illustrations/internet.svg'
		}
	];

	// Animation state for chat bubbles and image
	let showChat1 = false;
	let showChat2 = false;
	let showImage = false;
	let isFadingOut = false;

	// Track previous visibility for fade direction
	let wasChat1Visible = false;
	let wasChat2Visible = false;
	let wasImageVisible = false;

	// Watchers to update wasVisible flags
	$: if (showChat1 && !wasChat1Visible) wasChat1Visible = true;
	$: if (!showChat1 && wasChat1Visible)
		setTimeout(() => {
			wasChat1Visible = false;
		}, 700);

	$: if (showChat2 && !wasChat2Visible) wasChat2Visible = true;
	$: if (!showChat2 && wasChat2Visible)
		setTimeout(() => {
			wasChat2Visible = false;
		}, 700);

	$: if (showImage && !wasImageVisible) wasImageVisible = true;
	$: if (!showImage && wasImageVisible)
		setTimeout(() => {
			wasImageVisible = false;
		}, 700);

	let previousIndex = currentIndex;

	function startSequentialFadeIn() {
		showChat1 = false;
		showChat2 = false;
		showImage = false;
		setTimeout(() => {
			showChat1 = true;
		}, 200);
		setTimeout(() => {
			showChat2 = true;
		}, 600);
		setTimeout(() => {
			showImage = true;
		}, 900);
	}

	function fadeOutAndNextStep() {
		isFadingOut = true;
		showChat1 = false;
		showChat2 = false;
		showImage = false;
		setTimeout(() => {
			isFadingOut = false;
			previousIndex = currentIndex;
			currentIndex = (currentIndex + 1) % carouselItems.length;
			startSequentialFadeIn();
		}, 700);
	}

	// Only trigger fade-in sequence once per slide change
	$: if (loaded && currentIndex !== previousIndex && !isFadingOut) {
		// Do nothing, handled by fadeOutAndNextStep
	}

	// On initial load, start fade-in
	$: if (
		loaded &&
		previousIndex === currentIndex &&
		!showChat1 &&
		!showChat2 &&
		!showImage &&
		!isFadingOut
	) {
		startSequentialFadeIn();
	}

	let carouselInterval: ReturnType<typeof setInterval>;
	onMount(() => {
		carouselInterval = setInterval(() => {
			if (!isFadingOut) fadeOutAndNextStep();
		}, 7000);
		return () => clearInterval(carouselInterval);
	});

	const querystringValue = (key: string) => {
		const querystring = window.location.search;
		const urlParams = new URLSearchParams(querystring);
		return urlParams.get(key);
	};

	const setSessionUser = async (sessionUser: SessionUser) => {
		if (sessionUser) {
			console.log(sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.setItem('token', sessionUser.token);
			}

			$socket?.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			const redirectPath = querystringValue('redirect') || '/';
			goto(redirectPath);

			_paq.push(['trackEvent', 'Auth', 'OAuth Login Success']);
		} else {
			_paq.push(['trackEvent', 'Auth', 'OAuth Login Failed']);
		}
	};

	const signUpHandler = async () => {
		try {
			const sessionUser = await userSignUp(
				name,
				email,
				password,
				generateInitialsImage(name)
			).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			await setSessionUser(sessionUser);
		} catch (error) {
			console.error('Sign-up error:', error);
			const errorMsg = error instanceof Error ? error.message : String(error);
			toast.error(`Sign-up error: ${errorMsg}`);
		}
	};

	const submitHandler = async () => {
		await signUpHandler();
	};

	const checkOauthCallback = async () => {
		if (!$page.url.hash) {
			return;
		}
		const hash = $page.url.hash.substring(1);
		if (!hash) {
			return;
		}
		const params = new URLSearchParams(hash);
		const token = params.get('token');
		if (!token) {
			return;
		}

		localStorage.setItem('token', token);

		const sessionUser = await getSessionUser().catch((error) => {
			localStorage.removeItem('token'); // Clear token if getSessionUser fails
			toast.error(error);
			return null;
		});

		if (!sessionUser) {
			return;
		}

		$socket?.emit('user-join', { auth: { token: sessionUser.token } });
		await user.set(sessionUser);
		await config.set(await getBackendConfig());
		goto('/');

		_paq.push(['trackEvent', 'Auth', 'OAuth Login Success']);
	};

	async function setLogoImage() {
		await tick();
		const logo = document.getElementById('logo');

		if (logo) {
			const isDarkMode = document.documentElement.classList.contains('dark');

			if (isDarkMode) {
				const darkImage = new Image();
				darkImage.src = '/static/favicon-dark.png';

				darkImage.onload = () => {
					(logo as HTMLImageElement).src = '/static/favicon-dark.png';
					logo.style.filter = ''; // Ensure no inversion is applied if favicon-dark.png exists
				};

				darkImage.onerror = () => {
					logo.style.filter = 'invert(1)'; // Invert image if favicon-dark.png is missing
				};
			}
		}
	}

	onMount(async () => {
		if ($user !== undefined) {
			const redirectPath = querystringValue('redirect') || '/';
			goto(redirectPath);
		}

		await checkOauthCallback();

		loaded = true;
		setLogoImage();

		_paq.push(['trackPageView', 'Auth Page']);
	});
</script>

<svelte:head>
	<title>
		{`${$WEBUI_NAME}`}
	</title>
</svelte:head>

<Header />
<!-- Main container -->
<div class="w-full h-[100dvh] text-white overflow-auto">
	<!-- Background -->
	<div class="w-full h-full fixed top-0 left-0 bg-white dark:bg-black -z-10"></div>

	<!-- Drag region -->
	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<div class="min-h-full w-full flex flex-col">
			<div class="flex-1 flex items-center">
				<div class="w-full flex justify-center font-primary text-black dark:text-white pt-[5vh]">
					<div class="w-full px-10 flex flex-col text-center">
						<div class="w-full dark:text-gray-100">
							{#if $config?.onboarding}
								<form
									class="w-full max-w-md mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden p-6"
									on:submit={(e) => {
										e.preventDefault();
										submitHandler();
									}}
								>
									<div class="text-center mb-6">
										<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
											{$i18n.t(`Create Admin Account`)}
										</h1>
										<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
											{$i18n.t('Please fill in the details below to create your admin account.')}
										</p>
									</div>

									<div class="flex flex-col space-y-4">
										<div class="flex flex-col space-y-2">
											<label
												for="name"
												class="text-left text-sm font-medium text-gray-700 dark:text-gray-300"
											>
												{$i18n.t('Name')}
											</label>
											<input
												id="name"
												bind:value={name}
												type="text"
												class="px-3 text-left py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-white"
												autocomplete="name"
												placeholder={$i18n.t('Enter Your Full Name')}
												required
											/>
										</div>

										<div class="flex flex-col space-y-2">
											<label
												for="email"
												class="text-sm font-medium text-left text-gray-700 dark:text-gray-300"
											>
												{$i18n.t('Email')}
											</label>
											<input
												id="email"
												bind:value={email}
												type="email"
												class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-white"
												autocomplete="email"
												name="email"
												placeholder={$i18n.t('Enter Your Email')}
												required
											/>
										</div>

										<div class="flex flex-col space-y-2">
											<label
												for="password"
												class="text-sm font-medium text-left text-gray-700 dark:text-gray-300"
											>
												{$i18n.t('Password')}
											</label>
											<input
												id="password"
												bind:value={password}
												type="password"
												class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:text-white"
												placeholder={$i18n.t('Choose a Strong Password')}
												autocomplete="new-password"
												name="new-password"
												required
											/>
										</div>
									</div>

									<button
										type="submit"
										class="w-full mt-6 flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white fr-background-action-high--blue-france focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
									>
										{$i18n.t('Create Admin Account')}
									</button>
								</form>
							{:else}
								<div
									class="flex flex-col md:flex-row w-full gap-8 md:gap-16 items-center justify-center h-[95vh]"
								>
									<!-- Left column - Login content -->
									<div
										class="flex flex-col w-full md:w-1/2 gap-4 m-4 h-[calc(100%-1.5rem)] items-center justify-center"
									>
										<!-- Title section -->
										<div>
											<div class="w-full max-w-md mx-auto">
												<div class="pb-4 w-full dark:text-gray-100 text-center">
													<div class="flex flex-col gap-3 items-center text-center">
														<div
															class="text-2xl sm:text-4xl md:text-5xl fr-text-default--grey font-bold text-center"
														>
															{@html $i18n.t('ai_for_public_services').replace(/\n/g, '<br />')}
														</div>
													</div>
												</div>
											</div>
										</div>

										<!-- Login button -->
										<div class="w-full flex justify-center">
											<ProconnectButton
												on:click={() =>
													_paq.push(['trackEvent', 'Auth', 'ProConnect Button Click'])}
											/>
										</div>
									</div>

									<!-- Right column - Carousel -->
									<div
										class="w-full md:w-1/2 md:block bg-blue-50/60 rounded-xl m-4 h-[calc(100%-1.5rem)] flex items-center justify-center"
									>
										<div class="w-full flex flex-col items-center justify-center h-full relative">
											<div
												class="carousel-stack relative w-full flex flex-col items-center justify-center h-[340px]"
											>
												<div
													class="carousel-bubble-container absolute left-0 right-0 top-0 flex flex-col items-center justify-center w-full h-full pointer-events-none"
												>
													<div class="carousel-stack-inner">
														<div
															class="chat-bubble mb-4 z-30 transition-all duration-700"
															style="opacity: {showChat1 ? 1 : 0}; transform: translateY({showChat1
																? '0'
																: wasChat1Visible
																	? '40px'
																	: '-40px'}); position: relative; pointer-events: none;"
														>
															{carouselItems[currentIndex].chat1}
														</div>
														<div
															class="chat-bubble-secondary mb-4 z-20 transition-all duration-700"
															style="opacity: {showChat2 ? 1 : 0}; transform: translateY({showChat2
																? '0'
																: wasChat2Visible
																	? '40px'
																	: '-40px'}); position: relative; pointer-events: none;"
														>
															{carouselItems[currentIndex].chat2}
														</div>
														<div
															class="carousel-image z-10 transition-all rounded-4xl duration-700"
															style="opacity: {showImage ? 1 : 0}; transform: translateY({showImage
																? '0'
																: wasImageVisible
																	? '40px'
																	: '-40px'}); position: relative; pointer-events: none; margin-left: 180px;"
														>
															<img
																src={carouselItems[currentIndex].image}
																alt="carousel image"
																style="width: 400px; height: auto; max-width: none; max-height: none; display: block; border-radius: 1rem;"
															/>
														</div>
													</div>
												</div>
											</div>
										</div>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- Footer -->
			<div class="w-full fr-background-default--grey">
				<Footer />
			</div>
		</div>
	{:else}
		<div class="w-full h-full flex justify-center items-center font-primary">
			<Spinner />
		</div>
	{/if}
</div>

<style>
	.chat-bubble {
		background: #fff;
		color: #222;
		border-radius: 1.5rem;
		padding: 1rem 2rem;
		box-shadow: 0 2px 16px 0 rgba(0, 0, 0, 0.07);
		font-size: 1.15rem;
		font-weight: 500;
		max-width: 340px;
		text-align: left;
		min-height: 48px;
	}
	.chat-bubble-secondary {
		background: #e6f0ff;
		color: #222;
		border-radius: 1.5rem;
		padding: 1rem 2rem;
		box-shadow: 0 2px 16px 0 rgba(0, 0, 0, 0.04);
		font-size: 1.05rem;
		font-weight: 400;
		max-width: 320px;
		text-align: left;
		min-height: 44px;
	}
	.carousel-image {
		margin-top: 0.5rem;
		margin-left: 48px;
	}
	.carousel-stack {
		min-height: 340px;
		width: 100%;
		position: relative;
	}
	.carousel-bubble-container {
		width: 100%;
		height: 100%;
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		pointer-events: none;
	}
	.carousel-stack-inner {
		position: absolute;
		left: 50%;
		top: 0;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		width: auto;
		min-width: 0;
		max-width: none;
	}
</style>
