"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { fetchQuiz, type QuizResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Message =
	| { role: "system" | "user" | "assistant"; content: string }
	| { role: "quiz"; content: QuizResponse };

export default function ChatPage() {
	const [messages, setMessages] = useState<Message[]>([
		{ role: "system", content: "世界遺産クイズへようこそ。ボタンで問題を取得できます。" },
	]);
	const [loading, setLoading] = useState(false);
	const [answer, setAnswer] = useState("");

	const seenQuizIds = useMemo(() => {
		const ids: string[] = [];
		for (const m of messages) {
			if (m.role === "quiz" && m.content?.id) ids.push(m.content.id);
		}
		return ids;
	}, [messages]);

	const lastQuiz = useMemo(() => {
		for (let i = messages.length - 1; i >= 0; i--) {
			const m = messages[i];
			if (m.role === "quiz") return m.content as QuizResponse;
		}
		return undefined;
	}, [messages]);

	async function handleFetchQuiz() {
		try {
			setLoading(true);
			const q = await fetchQuiz(seenQuizIds);
			setMessages((prev) => [...prev, { role: "quiz", content: q }]);
			setAnswer("");
		} catch (err) {
			console.error(err);
			setMessages((prev) => [
				...prev,
				{ role: "assistant", content: "取得に失敗しました。バックエンドが起動しているか確認してください。" },
			]);
		} finally {
			setLoading(false);
		}
	}

	function handleSubmit() {
		if (!lastQuiz || !answer) return;
		const correct = answer === lastQuiz.answer;
		setMessages((prev) => [
			...prev,
			{ role: "user", content: `回答: ${answer}` },
			{ role: "assistant", content: correct ? "正解！" : `不正解… 正解は「${lastQuiz.answer}」` },
		]);
		setAnswer("");
	}

	return (
		<div className="min-h-screen flex flex-col bg-background text-foreground">
			<header className="border-b px-4 py-3 sticky top-0 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
				<div className="max-w-3xl mx-auto flex items-center justify-between">
					<h1 className="font-semibold">世界遺産クイズ</h1>
					<div className="text-xs text-muted-foreground">作者：ららかちゃん</div>
				</div>
			</header>
			<main className="flex-1">
				<div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
					{messages.map((m, idx) => (
						<div key={idx} className="flex gap-3 items-start">
							<div className={`rounded-full size-8 shrink-0 flex items-center justify-center border ${m.role === "user" ? "bg-primary text-primary-foreground" : m.role === "assistant" ? "bg-secondary text-secondary-foreground" : "bg-muted"}`}>
								{m.role === "user" ? "U" : m.role === "assistant" ? "A" : m.role === "quiz" ? "Q" : "S"}
							</div>
							<div className="flex-1">
								{m.role === "quiz" ? (
									<div className="space-y-3">
										<div className="font-medium">{m.content.question}</div>
										<div className="relative w-full max-w-md aspect-video overflow-hidden rounded border bg-black/5">
											<Image src={m.content.image_url} alt="quiz" fill className="object-contain" />
										</div>
										<div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
											{m.content.options.map((opt) => (
												<Button key={opt} variant="outline" onClick={() => setAnswer(opt)} className={answer === opt ? "border-primary" : ""}>
													{opt}
												</Button>
											))}
										</div>
									</div>
								) : (
									<div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
								)}
							</div>
						</div>
					))}
				</div>
			</main>
			<footer className="border-t">
				<div className="max-w-3xl mx-auto px-4 py-3 flex gap-2 items-center">
					<Button onClick={handleFetchQuiz} disabled={loading}>
						{loading ? "取得中..." : "問題を取得"}
					</Button>
					<Input placeholder="選択肢をクリック、または入力" value={answer} onChange={(e) => setAnswer(e.target.value)} />
					<Button variant="secondary" onClick={handleSubmit} disabled={!lastQuiz || !answer}>
						回答する
					</Button>
				</div>
			</footer>
		</div>
	);
}
