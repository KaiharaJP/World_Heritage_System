export type QuizResponse = {
	question: string;
	image_url: string;
	options: string[];
	answer: string;
};

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchQuiz(baseUrl: string = DEFAULT_BASE_URL): Promise<QuizResponse> {
	const res = await fetch(`${baseUrl}/quiz`, { cache: "no-store" });
	if (!res.ok) {
		throw new Error(`Failed to fetch quiz: ${res.status}`);
	}
	return res.json();
}
