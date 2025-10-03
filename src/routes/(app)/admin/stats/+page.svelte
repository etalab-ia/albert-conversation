<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// TEMPORARY DISABLE: Stats endpoint causing database performance issues
	// Redirect users away from stats page
	onMount(() => {
		goto('/admin', { replaceState: true });
	});
</script>

<svelte:head>
	<title>Statistiques temporairement indisponibles | Assistant IA</title>
</svelte:head>

<div class="flex items-center justify-center min-h-screen">
	<div class="text-center">
		<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
			Statistiques temporairement indisponibles
		</h1>
		<p class="text-gray-600 dark:text-gray-400 mb-6">
			Les statistiques sont temporairement désactivées pour des raisons de performance.
		</p>
		<a 
			href="/admin" 
			class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 transition-colors"
		>
			← Retour à l'administration
		</a>
	</div>
</div>