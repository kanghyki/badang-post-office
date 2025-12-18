"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "../write/write.module.scss";
import Header from "@/app/components/Header";
import TemplateImageModal from "@/app/components/TemplateImageModal";
import { postcardsApi } from "@/lib/api/postcards";
import {
    templatesApi,
    TemplateResponse,
    TemplateDetailResponse,
} from "@/lib/api/templates";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/app/context/NotificationContext";
import { ROUTES, API_BASE_URL } from "@/lib/constants/urls";
import { fetchImageWithAuth } from "@/lib/utils/image";

function ModifyContent() {
    useAuth(); // 인증 체크
    const router = useRouter();
    const { showToast, showModal } = useNotification();
    const searchParams = useSearchParams();
    const postcardId = searchParams.get("id");

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const [text, setText] = useState("");
    const [translatedText, setTranslatedText] = useState("");
    const [recipientName, setRecipientName] = useState("");
    const [emailLocalPart, setEmailLocalPart] = useState("");
    const [emailDomain, setEmailDomain] = useState("");
    const [selectedDomain, setSelectedDomain] = useState("");
    const [customDomain, setCustomDomain] = useState("");
    const [senderName, setSenderName] = useState("");

    // 이메일 도메인 옵션
    const emailDomains = ["gmail.com", "naver.com", "daum.net", "kakao.com"];
    const [scheduledAt, setScheduledAt] = useState("");
    const [sendType, setSendType] = useState<"immediate" | "scheduled">(
        "immediate"
    );
    const [image, setImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string>("");
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const [templates, setTemplates] = useState<TemplateResponse[]>([]);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
    const [loadingTemplates, setLoadingTemplates] = useState(true);
    const [templateImageUrls, setTemplateImageUrls] = useState<
        Record<string, string>
    >({});
    const [selectedTemplateDetail, setSelectedTemplateDetail] =
        useState<TemplateDetailResponse | null>(null);
    const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

    // 템플릿 확대 모달 상태
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [selectedTemplateImageUrl, setSelectedTemplateImageUrl] = useState<
        string | null
    >(null);

    // 이메일 도메인 선택 처리
    useEffect(() => {
        if (selectedDomain === "custom") {
            setEmailDomain(customDomain);
        } else if (selectedDomain) {
            setEmailDomain(selectedDomain);
        }
    }, [selectedDomain, customDomain]);

    // 입력값 변경 감지
    useEffect(() => {
        if (
            text ||
            recipientName ||
            emailLocalPart ||
            emailDomain ||
            senderName ||
            scheduledAt ||
            image
        ) {
            setHasUnsavedChanges(true);
        }
    }, [
        text,
        recipientName,
        emailLocalPart,
        emailDomain,
        senderName,
        scheduledAt,
        image,
    ]);

    // 뒤로가기 시 경고
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = "";
            }
        };

        window.addEventListener("beforeunload", handleBeforeUnload);
        return () =>
            window.removeEventListener("beforeunload", handleBeforeUnload);
    }, [hasUnsavedChanges]);

    // 템플릿 목록 불러오기
    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                setLoadingTemplates(true);
                const response = await templatesApi.getList();
                setTemplates(response.templates);

                // 각 템플릿의 이미지를 인증과 함께 불러오기
                const imageUrls: Record<string, string> = {};
                await Promise.all(
                    response.templates.map(async (template) => {
                        try {
                            const imageUrl = `${API_BASE_URL}${template.template_image_path}`;
                            const blobUrl = await fetchImageWithAuth(imageUrl);
                            imageUrls[template.id] = blobUrl;
                        } catch (error) {
                            console.error(
                                `템플릿 ${template.id} 이미지 로드 실패:`,
                                error
                            );
                        }
                    })
                );
                setTemplateImageUrls(imageUrls);
            } catch (error) {
                console.error("템플릿 목록 불러오기 실패:", error);
                showToast({
                    message: "템플릿을 불러오는데 실패했습니다.",
                    type: "error",
                });
            } finally {
                setLoadingTemplates(false);
            }
        };

        fetchTemplates();

        // cleanup: blob URL 해제
        return () => {
            Object.values(templateImageUrls).forEach((url) => {
                if (url) {
                    URL.revokeObjectURL(url);
                }
            });
        };
    }, [showToast]);

    // 선택된 템플릿의 상세 정보 가져오기
    useEffect(() => {
        const fetchTemplateDetail = async () => {
            if (!selectedTemplateId) return;

            try {
                const detail = await templatesApi.getById(selectedTemplateId);
                setSelectedTemplateDetail(detail);
                console.log("템플릿 상세 정보:", detail);
            } catch (error) {
                console.error("템플릿 상세 정보 로드 실패:", error);
                showToast({
                    message: "템플릿 설정을 불러오는데 실패했습니다.",
                    type: "error",
                });
            }
        };

        fetchTemplateDetail();
    }, [selectedTemplateId, showToast]);

    // 기존 엽서 데이터 로드
    useEffect(() => {
        if (!postcardId) {
            showModal({
                title: "오류",
                message: "엽서 ID가 없습니다.",
                type: "alert",
            }).then(() => {
                router.push(ROUTES.LIST);
            });
            return;
        }

        const loadPostcard = async () => {
            try {
                setInitialLoading(true);
                const postcard = await postcardsApi.getById(postcardId);

                // 현재 템플릿 ID 설정
                setSelectedTemplateId(postcard.template_id);

                // 상태가 writing이나 pending일 때만 수정 가능
                if (
                    postcard.status !== "writing" &&
                    postcard.status !== "pending"
                ) {
                    await showModal({
                        title: "수정 불가",
                        message:
                            "이미 발송되었거나 발송 중인 엽서는 수정할 수 없습니다.",
                        type: "alert",
                    });
                    router.push(ROUTES.LIST);
                    return;
                }

                setText(postcard.original_text || "");
                setTranslatedText(postcard.text || "");
                setRecipientName(postcard.recipient_name || "");

                // 이메일을 @ 기준으로 분리
                if (postcard.recipient_email) {
                    const [local, domain] = postcard.recipient_email.split("@");
                    setEmailLocalPart(local || "");
                    setEmailDomain(domain || "");

                    // 도메인이 목록에 있는지 확인하고 설정
                    const domainList = [
                        "gmail.com",
                        "naver.com",
                        "daum.net",
                        "kakao.com",
                        "hanmail.net",
                        "nate.com",
                        "outlook.com",
                        "yahoo.com",
                    ];

                    if (domain && domainList.includes(domain)) {
                        setSelectedDomain(domain);
                    } else if (domain) {
                        setSelectedDomain("custom");
                        setCustomDomain(domain);
                    }
                }

                setSenderName(postcard.sender_name || "");

                if (postcard.scheduled_at) {
                    // ISO 8601을 datetime-local 형식으로 변환
                    const date = new Date(postcard.scheduled_at);
                    const localDateTime = new Date(
                        date.getTime() - date.getTimezoneOffset() * 60000
                    )
                        .toISOString()
                        .slice(0, 16);
                    setScheduledAt(localDateTime);
                    setSendType("scheduled");
                } else {
                    setSendType("immediate");
                }

                // 사용자가 업로드한 사진이 있는 경우 미리보기 표시
                if (postcard.user_photo_url) {
                    try {
                        const imageUrl = `${API_BASE_URL}${postcard.user_photo_url}`;
                        const blobUrl = await fetchImageWithAuth(imageUrl);
                        setImagePreview(blobUrl);
                    } catch (error) {
                        console.error("사용자 업로드 이미지 로드 실패:", error);
                    }
                }
            } catch (error) {
                console.error("엽서 로드 실패:", error);
                await showModal({
                    title: "오류",
                    message: "엽서를 불러올 수 없습니다.",
                    type: "alert",
                });
                router.push(ROUTES.LIST);
            } finally {
                setInitialLoading(false);
            }
        };

        loadPostcard();
    }, [postcardId, router]);

    // 이미지 파일 선택
    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setImage(file);

        const reader = new FileReader();
        reader.onloadend = () => {
            setImagePreview(reader.result as string);
        };
        reader.readAsDataURL(file);
    };

    // 이미지 삭제
    const handleImageRemove = () => {
        setImage(null);
        setImagePreview("");
        // input 파일도 초기화
        const fileInput = document.getElementById(
            "imageInput"
        ) as HTMLInputElement;
        if (fileInput) {
            fileInput.value = "";
        }
    };

    // 저장 (update만 호출)
    const handleSave = useCallback(
        async (isAutoSave = false) => {
            if (!postcardId) {
                await showModal({
                    title: "오류",
                    message: "엽서 ID가 없습니다.",
                    type: "alert",
                });
                return;
            }

            // 이메일 validation
            if (emailLocalPart || emailDomain) {
                if (!emailLocalPart || !emailDomain) {
                    showToast({
                        message: "이메일 주소를 완성해주세요.",
                        type: "error",
                    });
                    return;
                }
                if (!/^[a-zA-Z0-9._-]+$/.test(emailLocalPart)) {
                    showToast({
                        message: "유효한 이메일 형식이 아닙니다.",
                        type: "error",
                    });
                    return;
                }
                if (!/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(emailDomain)) {
                    showToast({
                        message: "유효한 도메인 형식이 아닙니다.",
                        type: "error",
                    });
                    return;
                }
            }

            setSaving(true);

            try {
                // 이메일 주소 조합
                const recipientEmail =
                    emailLocalPart && emailDomain
                        ? `${emailLocalPart}@${emailDomain}`
                        : undefined;

                const updatedPostcard = await postcardsApi.update(postcardId, {
                    template_id: selectedTemplateId,
                    text,
                    recipient_email: recipientEmail,
                    recipient_name: recipientName,
                    sender_name: senderName,
                    scheduled_at:
                        sendType === "scheduled" && scheduledAt
                            ? new Date(scheduledAt).toISOString()
                            : undefined,
                    image: image || undefined,
                });

                // 서버에서 번역된 텍스트를 미리보기에 표시
                if (updatedPostcard.text) {
                    setTranslatedText(updatedPostcard.text);
                }

                setHasUnsavedChanges(false);
                if (!isAutoSave) {
                    showToast({
                        message: "임시 저장되었습니다.",
                        type: "success",
                    });
                }
            } catch (error) {
                console.error("저장 실패:", error);
                if (!isAutoSave) {
                    if (error instanceof Error) {
                        showToast({
                            message: `저장 실패: ${error.message}`,
                            type: "error",
                        });
                    } else {
                        showToast({
                            message: "저장 중 오류가 발생했습니다.",
                            type: "error",
                        });
                    }
                }
            } finally {
                setSaving(false);
            }
        },
        [
            postcardId,
            selectedTemplateId,
            text,
            recipientName,
            emailLocalPart,
            emailDomain,
            senderName,
            sendType,
            scheduledAt,
            image,
            showToast,
            showModal,
        ]
    );

    // 디바운싱을 적용한 자동 저장
    useEffect(() => {
        // 타이머가 있으면 클리어
        if (autoSaveTimerRef.current) {
            clearTimeout(autoSaveTimerRef.current);
        }

        // 입력된 내용이 있고, 저장 중이 아닐 때만 자동 저장 타이머 설정
        if (hasUnsavedChanges && !saving && !loading) {
            autoSaveTimerRef.current = setTimeout(() => {
                handleSave(true);
            }, 1000);
        }

        // cleanup
        return () => {
            if (autoSaveTimerRef.current) {
                clearTimeout(autoSaveTimerRef.current);
            }
        };
    }, [
        text,
        recipientName,
        emailLocalPart,
        emailDomain,
        senderName,
        scheduledAt,
        image,
        selectedTemplateId,
        hasUnsavedChanges,
        saving,
        loading,
        handleSave,
    ]);

    // 다시 접수하기 (update + send 호출)
    const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        if (!postcardId) {
            await showModal({
                title: "오류",
                message: "엽서 ID가 없습니다.",
                type: "alert",
            });
            return;
        }

        // 이메일 validation
        if (!emailLocalPart || !emailDomain) {
            showToast({
                message: "이메일 주소를 입력해주세요.",
                type: "error",
            });
            return;
        }
        if (!/^[a-zA-Z0-9._-]+$/.test(emailLocalPart)) {
            showToast({
                message: "유효한 이메일 형식이 아닙니다.",
                type: "error",
            });
            return;
        }
        if (!/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(emailDomain)) {
            showToast({
                message: "유효한 도메인 형식이 아닙니다.",
                type: "error",
            });
            return;
        }

        // 예약 발송 시 날짜 validation
        if (sendType === "scheduled" && !scheduledAt) {
            showToast({ message: "발송 일시를 선택해주세요.", type: "error" });
            return;
        }

        setLoading(true);

        try {
            // 이메일 주소 조합
            const recipientEmail = `${emailLocalPart}@${emailDomain}`;

            // 1. 엽서 내용 업데이트
            await postcardsApi.update(postcardId, {
                template_id: selectedTemplateId,
                text,
                recipient_email: recipientEmail,
                recipient_name: recipientName,
                sender_name: senderName,
                scheduled_at:
                    sendType === "scheduled" && scheduledAt
                        ? new Date(scheduledAt).toISOString()
                        : undefined,
                image: image || undefined,
            });

            // 2. 엽서 발송
            await postcardsApi.send(postcardId);

            setHasUnsavedChanges(false);
            router.push(ROUTES.LIST);
        } catch (error) {
            console.error("엽서 전송 실패:", error);
            if (error instanceof Error) {
                showToast({
                    message: `전송 실패: ${error.message}`,
                    type: "error",
                });
            } else {
                showToast({
                    message: "전송 중 오류가 발생했습니다.",
                    type: "error",
                });
            }
        } finally {
            setLoading(false);
        }
    };

    if (initialLoading || (loadingTemplates && !selectedTemplateId)) {
        return (
            <>
                <div className="hdrWrap">
                    <Header title="엽서 수정하기" />
                </div>
                <div className="container"></div>
            </>
        );
    }

    return (
        <>
            <div className="hdrWrap">
                <Header title="엽서 수정하기" />
            </div>

            <div className="container">
                <main className={styles.writeMain}>
                    <form onSubmit={handleSend} id="postcardForm">
                        {/* 템플릿 선택 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>템플릿 선택</h3>
                            {loadingTemplates ? (
                                <div className={styles.templateLoading}>
                                    <span
                                        className={styles.smallSpinner}
                                    ></span>
                                    <span>템플릿을 불러오는 중...</span>
                                </div>
                            ) : templates.length === 0 ? (
                                <div className={styles.templateEmpty}>
                                    사용 가능한 템플릿이 없습니다.
                                </div>
                            ) : (
                                <div className={styles.templateGrid}>
                                    {templates.map((template) => (
                                        <label
                                            key={template.id}
                                            className={`${
                                                styles.templateCard
                                            } ${
                                                selectedTemplateId ===
                                                template.id
                                                    ? styles.selected
                                                    : ""
                                            }`}
                                        >
                                            <input
                                                type="radio"
                                                name="template"
                                                value={template.id}
                                                checked={
                                                    selectedTemplateId ===
                                                    template.id
                                                }
                                                onChange={(e) =>
                                                    setSelectedTemplateId(
                                                        e.target.value
                                                    )
                                                }
                                                className={styles.templateRadio}
                                            />
                                            <div
                                                className={
                                                    styles.templateImageWrapper
                                                }
                                            >
                                                {templateImageUrls[
                                                    template.id
                                                ] ? (
                                                    <>
                                                        <img
                                                            src={
                                                                templateImageUrls[
                                                                    template.id
                                                                ]
                                                            }
                                                            alt={template.name}
                                                            className={
                                                                styles.templateImage
                                                            }
                                                        />
                                                        <button
                                                            type="button"
                                                            className={
                                                                styles.expandButton
                                                            }
                                                            onClick={(e) => {
                                                                e.preventDefault();
                                                                e.stopPropagation();
                                                                setSelectedTemplateImageUrl(
                                                                    templateImageUrls[
                                                                        template
                                                                            .id
                                                                    ]
                                                                );
                                                                setIsTemplateModalOpen(
                                                                    true
                                                                );
                                                            }}
                                                            aria-label="템플릿 확대"
                                                        >
                                                            ⤢
                                                        </button>
                                                    </>
                                                ) : (
                                                    <div
                                                        className={
                                                            styles.templateImageLoading
                                                        }
                                                    >
                                                        <span
                                                            className={
                                                                styles.smallSpinner
                                                            }
                                                        ></span>
                                                    </div>
                                                )}
                                            </div>
                                            <div
                                                className={styles.templateInfo}
                                            >
                                                <div
                                                    className={
                                                        styles.templateName
                                                    }
                                                >
                                                    {template.name}
                                                </div>
                                                {template.description && (
                                                    <div
                                                        className={
                                                            styles.templateDescription
                                                        }
                                                    >
                                                        {template.description}
                                                    </div>
                                                )}
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* 엽서 내용 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>*엽서 내용</h3>
                            <div className={styles.textBox}>
                                <div className={styles.textareaWrapper}>
                                    <textarea
                                        value={text}
                                        onChange={(e) =>
                                            setText(e.target.value)
                                        }
                                        placeholder="내용 작성해주세요."
                                        maxLength={120}
                                        className={styles.textarea}
                                        required
                                    />
                                    <span className={styles.charCount}>
                                        {text.length} / 120
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* 이미지 업로드 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>사진 첨부</h3>
                            {!imagePreview ? (
                                <div className={styles.fileInputWrapper}>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handleImageChange}
                                        className={styles.fileInput}
                                        id="imageInput"
                                    />
                                    <label
                                        htmlFor="imageInput"
                                        className={styles.fileLabel}
                                    >
                                        <span className={styles.uploadText}>
                                            사진을 선택해주세요
                                        </span>
                                        <span className={styles.uploadHint}>
                                            클릭하여 사진 업로드
                                        </span>
                                    </label>
                                </div>
                            ) : (
                                <div className={styles.imagePreviewContainer}>
                                    <div className={styles.previewBox}>
                                        <img
                                            src={imagePreview}
                                            alt="preview"
                                            className={styles.previewImg}
                                        />
                                        <button
                                            type="button"
                                            onClick={handleImageRemove}
                                            className={styles.removeImageBtn}
                                            aria-label="사진 삭제"
                                        >
                                            <svg
                                                width="20"
                                                height="20"
                                                viewBox="0 0 20 20"
                                                fill="none"
                                                xmlns="http://www.w3.org/2000/svg"
                                            >
                                                <path
                                                    d="M15 5L5 15M5 5L15 15"
                                                    stroke="currentColor"
                                                    strokeWidth="2"
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                        </button>
                                    </div>
                                    {image && (
                                        <p className={styles.imageName}>
                                            {image.name}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* 받는 사람 정보 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>*받는 사람</h3>
                            <div className={styles.inputGroup}>
                                <label className={styles.inputLabel}>
                                    <span className={styles.icon}>👤</span>
                                    <input
                                        type="text"
                                        value={recipientName}
                                        onChange={(e) =>
                                            setRecipientName(e.target.value)
                                        }
                                        placeholder="예) 사랑하는 어머니 (수신자명)"
                                        className={styles.input}
                                        required
                                    />
                                </label>
                            </div>

                            <div className={styles.inputGroup}>
                                <label className={styles.inputLabel}>
                                    <span className={styles.icon}>📧</span>
                                    <div className={styles.emailInputWrapper}>
                                        <input
                                            type="text"
                                            value={emailLocalPart}
                                            onChange={(e) =>
                                                setEmailLocalPart(
                                                    e.target.value
                                                )
                                            }
                                            placeholder="이메일"
                                            className={styles.emailInput}
                                            required
                                        />
                                        <span className={styles.atSymbol}>
                                            @
                                        </span>
                                        {selectedDomain === "custom" ? (
                                            <>
                                                <input
                                                    type="text"
                                                    value={customDomain}
                                                    onChange={(e) =>
                                                        setCustomDomain(
                                                            e.target.value
                                                        )
                                                    }
                                                    placeholder="example.com"
                                                    className={
                                                        styles.emailInput
                                                    }
                                                    required
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setSelectedDomain("");
                                                        setCustomDomain("");
                                                    }}
                                                    className={
                                                        styles.cancelCustomBtn
                                                    }
                                                    title="이메일 선택으로 돌아가기"
                                                >
                                                    ✕
                                                </button>
                                            </>
                                        ) : (
                                            <select
                                                value={selectedDomain}
                                                onChange={(e) =>
                                                    setSelectedDomain(
                                                        e.target.value
                                                    )
                                                }
                                                className={
                                                    styles.emailDomainSelect
                                                }
                                                required
                                            >
                                                <option value="">이메일</option>
                                                {emailDomains.map((domain) => (
                                                    <option
                                                        key={domain}
                                                        value={domain}
                                                    >
                                                        {domain}
                                                    </option>
                                                ))}
                                                <option value="custom">
                                                    직접 입력
                                                </option>
                                            </select>
                                        )}
                                    </div>
                                </label>
                            </div>
                        </div>

                        {/* 보내는 사람 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>보내는 사람</h3>
                            <div className={styles.inputGroup}>
                                <label className={styles.inputLabel}>
                                    <span className={styles.icon}>✍️</span>
                                    <input
                                        type="text"
                                        value={senderName}
                                        onChange={(e) =>
                                            setSenderName(e.target.value)
                                        }
                                        placeholder="예) 바당이 (발신자명)"
                                        className={styles.input}
                                    />
                                </label>
                            </div>
                        </div>

                        {/* 발송 방식 섹션 */}
                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>전달 시간</h3>

                            <div className={styles.sendTypeOptions}>
                                <label
                                    className={`${styles.sendTypeOption} ${
                                        sendType === "immediate"
                                            ? styles.active
                                            : ""
                                    }`}
                                >
                                    <input
                                        type="radio"
                                        name="sendType"
                                        value="immediate"
                                        checked={sendType === "immediate"}
                                        onChange={(e) =>
                                            setSendType(
                                                e.target.value as "immediate"
                                            )
                                        }
                                        className={styles.radioInput}
                                    />
                                    <div className={styles.optionContent}>
                                        <div className={styles.optionText}>
                                            <div className={styles.optionTitle}>
                                                바로 전달
                                            </div>
                                            <div
                                                className={
                                                    styles.optionDescription
                                                }
                                            >
                                                접수 즉시 전달
                                            </div>
                                        </div>
                                    </div>
                                </label>

                                <label
                                    className={`${styles.sendTypeOption} ${
                                        sendType === "scheduled"
                                            ? styles.active
                                            : ""
                                    }`}
                                >
                                    <input
                                        type="radio"
                                        name="sendType"
                                        value="scheduled"
                                        checked={sendType === "scheduled"}
                                        onChange={(e) =>
                                            setSendType(
                                                e.target.value as "scheduled"
                                            )
                                        }
                                        className={styles.radioInput}
                                    />
                                    <div className={styles.optionContent}>
                                        <div className={styles.optionText}>
                                            <div className={styles.optionTitle}>
                                                예약 전달
                                            </div>
                                            <div
                                                className={
                                                    styles.optionDescription
                                                }
                                            >
                                                날짜와 시간 선택
                                            </div>
                                        </div>
                                    </div>
                                </label>
                            </div>

                            {sendType === "scheduled" && (
                                <div className={styles.scheduledDateWrapper}>
                                    <label className={styles.dateInputLabel}>
                                        <span className={styles.dateLabel}>
                                            발송 일시
                                        </span>
                                        <input
                                            id="scheduled_at"
                                            type="datetime-local"
                                            value={scheduledAt}
                                            onChange={(e) =>
                                                setScheduledAt(e.target.value)
                                            }
                                            className={styles.dateInput}
                                            required
                                        />
                                    </label>
                                </div>
                            )}
                        </div>
                    </form>

                    <div className={styles.buttonSection}>
                        <button
                            className={styles.sendBtn}
                            type="submit"
                            form="postcardForm"
                            disabled={loading || saving}
                        >
                            {loading ? (
                                <>
                                    <span className={styles.spinner}></span>
                                    <span>보내는 중...</span>
                                </>
                            ) : (
                                <span>접수하기</span>
                            )}
                        </button>
                    </div>
                </main>

                {/* 템플릿 확대 모달 */}
                <TemplateImageModal
                    isOpen={isTemplateModalOpen}
                    onClose={() => setIsTemplateModalOpen(false)}
                    templateImageUrl={selectedTemplateImageUrl}
                />
            </div>
        </>
    );
}

export default function Modify() {
    return (
        <Suspense
            fallback={
                <>
                    <div className="hdrWrap">
                        <Header title="엽서 수정하기" />
                    </div>
                    <div className="container"></div>
                </>
            }
        >
            <ModifyContent />
        </Suspense>
    );
}
