import { useEffect, useState } from 'react';
import { API_BASE_URL, POSTCARD_ENDPOINTS } from '@/lib/constants/urls';
import { SendingStatus } from '@/lib/api/postcards';

interface PostcardStreamData {
  status: SendingStatus;
  error?: string;
}

interface UsePostcardStreamResult {
  sendingStatus: SendingStatus | null;
  error: string | null;
  isConnected: boolean;
}

/**
 * 엽서 발송 프로세스 상태를 SSE로 실시간 수신하는 훅
 *
 * @param postcardId - 엽서 ID
 * @param enabled - SSE 연결 활성화 여부 (기본값: true)
 * @returns 발송 상태, 에러 메시지, 연결 상태
 */
export function usePostcardStream(postcardId: string | null, enabled: boolean = true): UsePostcardStreamResult {
  const [sendingStatus, setSendingStatus] = useState<SendingStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // postcardId가 없거나 비활성화되면 연결하지 않음
    if (!postcardId || !enabled) {
      return;
    }

    // 이미 완료/실패 상태면 연결하지 않음
    if (sendingStatus === 'completed' || sendingStatus === 'failed') {
      return;
    }

    // 액세스 토큰 가져오기
    const token = localStorage.getItem('accessToken');
    if (!token) {
      setError('인증 토큰이 없습니다.');
      return;
    }

    // SSE URL 생성
    const streamUrl = `${API_BASE_URL}${POSTCARD_ENDPOINTS.STREAM(postcardId)}`;

    // AbortController로 연결 취소 관리
    const abortController = new AbortController();

    // fetch API로 SSE 스트림 읽기 (커스텀 헤더 지원)
    const connectSSE = async () => {
      try {
        // AbortSignal 체크: 이미 취소되었으면 실행하지 않음
        if (abortController.signal.aborted) {
          console.log('SSE 연결 취소됨 (시작 전):', postcardId);
          return;
        }

        console.log('SSE 연결 시작:', postcardId);

        const response = await fetch(streamUrl, {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'text/event-stream',
          },
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        setIsConnected(true);
        setError(null);
        console.log('SSE 연결됨:', postcardId);

        // ReadableStream으로 SSE 데이터 읽기
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('ReadableStream을 사용할 수 없습니다.');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log('SSE 스트림 종료:', postcardId);
            setIsConnected(false);
            break;
          }

          // 청크 디코딩 및 버퍼에 추가
          buffer += decoder.decode(value, { stream: true });

          // SSE 메시지 파싱 (data: {...}\n\n 형식)
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || ''; // 마지막 불완전한 메시지는 버퍼에 유지

          for (const message of messages) {
            if (message.startsWith('data: ')) {
              const dataStr = message.substring(6); // "data: " 제거
              try {
                const data: PostcardStreamData = JSON.parse(dataStr);
                console.log('🔔 SSE 메시지 수신:', data);

                // 상태 업데이트 (즉시 실행)
                setSendingStatus(prev => {
                  console.log('📝 sendingStatus 업데이트:', prev, '→', data.status);
                  return data.status;
                });

                if (data.status === 'failed' && data.error) {
                  setError(data.error);
                }

                // 완료/실패 시 연결 종료
                if (data.status === 'completed' || data.status === 'failed') {
                  reader.cancel();
                  setIsConnected(false);
                  return;
                }
              } catch (err) {
                console.error('SSE 메시지 파싱 오류:', err);
                setError('메시지 파싱 중 오류가 발생했습니다.');
              }
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name === 'AbortError') {
          console.log('SSE 연결 취소됨:', postcardId);
        } else {
          console.error('SSE 연결 오류:', err);
          const errorMessage = err instanceof Error ? err.message : '실시간 연결 중 오류가 발생했습니다.';
          setError(errorMessage);
        }
        setIsConnected(false);
      }
    };

    connectSSE();

    // 클린업: 컴포넌트 언마운트 또는 재렌더링 시 이전 연결 취소
    return () => {
      console.log('SSE 연결 정리:', postcardId);
      abortController.abort();
      setIsConnected(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postcardId, enabled]); // sendingStatus 제거 - 상태 변경 시 재연결 방지

  return {
    sendingStatus,
    error,
    isConnected,
  };
}
