/**
 * 인증이 필요한 이미지를 fetch하여 Blob URL로 변환
 */
export const fetchImageWithAuth = async (url: string): Promise<string> => {
  const token = localStorage.getItem('accessToken');

  const response = await fetch(url, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch image: ${response.status}`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
};
