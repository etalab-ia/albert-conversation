import { WEBUI_API_BASE_URL } from '$lib/constants';

export type TimePeriod = '1w' | '1m' | '3m' | '6m' | 'all';

export const getStatsData = async (token?: string, period: TimePeriod = 'all') => {
	let error = null;

	const headers: Record<string, string> = {
		'Content-Type': 'application/json'
	};

	// Only add authorization header if token is provided
	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}

	let res;
	try {
		const url = new URL(`${WEBUI_API_BASE_URL}/stats/`);
		url.searchParams.append('period', period);

		const response = await fetch(url.toString(), {
			method: 'GET',
			headers,
			credentials: 'include'
		});
		const data = await response.json();
		if (!response.ok) {
			throw data;
		}
		res = data;
		
	} catch (err: unknown) {
		console.log(err);
		error = err instanceof Error ? err.message : 'An unknown error occurred while fetching stats';
		res = null;
	}
	return { error, ...res };
};
