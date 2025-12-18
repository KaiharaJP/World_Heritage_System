export type QuizResponse = {
	id: string;
	question: string;
	image_url: string;
	options: string[];
	answer: string;
};

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchQuiz(
	excludeIds: string[] = [],
	baseUrl: string = DEFAULT_BASE_URL,
): Promise<QuizResponse> {
	const url = new URL(`${baseUrl}/quiz`);
	if (excludeIds.length > 0) {
		url.searchParams.set("exclude", excludeIds.join(","));
	}
	const res = await fetch(url.toString(), { cache: "no-store" });
	if (!res.ok) {
		throw new Error(`Failed to fetch quiz: ${res.status}`);
	}
	return res.json();
}
