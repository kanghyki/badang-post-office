"use client";

import { useState } from "react";

export default function Home() {
    const [inputText, setInputText] = useState("");
    const [translatedText, setTranslatedText] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const handleTranslate = async () => {
        if (!inputText.trim()) {
            setError("번역할 텍스트를 입력해주세요.");
            return;
        }

        setIsLoading(true);
        setError("");
        setTranslatedText("");

        try {
            const response = await fetch(
                `${
                    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                }/translate`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ text: inputText }),
                }
            );

            if (!response.ok) {
                throw new Error("번역에 실패했습니다.");
            }

            const data = await response.json();
            setTranslatedText(data.translated);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "번역 중 오류가 발생했습니다."
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4">
            <main className="w-full max-w-4xl">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 md:p-12">
                    {/* 헤더 */}
                    <div className="text-center mb-8">
                        <h1 className="text-4xl md:text-5xl font-bold text-gray-800 dark:text-white mb-3">
                            제주어 번역기
                        </h1>
                        <p className="text-gray-600 dark:text-gray-300 text-lg">
                            표준어를 제주 방언으로 번역해보세요
                        </p>
                    </div>

                    {/* 번역 영역 */}
                    <div className="space-y-6">
                        {/* 입력 영역 */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                                표준어 입력
                            </label>
                            <textarea
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder="예: 안녕하세요, 오늘 날씨가 좋네요"
                                className="w-full h-32 px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-700 text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-all"
                                disabled={isLoading}
                            />
                        </div>

                        {/* 번역 버튼 */}
                        <button
                            onClick={handleTranslate}
                            disabled={isLoading || !inputText.trim()}
                            className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg
                                        className="animate-spin h-5 w-5"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                            fill="none"
                                        />
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        />
                                    </svg>
                                    번역 중...
                                </span>
                            ) : (
                                "제주어로 번역하기"
                            )}
                        </button>

                        {/* 에러 메시지 */}
                        {error && (
                            <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4 rounded-r-xl">
                                <p className="text-red-700 dark:text-red-300 font-medium">
                                    {error}
                                </p>
                            </div>
                        )}

                        {/* 번역 결과 */}
                        {translatedText && (
                            <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-6 border-2 border-green-200 dark:border-green-700">
                                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                                    제주어 번역 결과
                                </label>
                                <p className="text-xl text-gray-800 dark:text-white font-medium leading-relaxed">
                                    {translatedText}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
