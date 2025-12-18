import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authUtils } from '@/lib/utils/auth';
import { ROUTES } from '@/lib/constants/urls';

export function useAuth(redirectTo: string = ROUTES.LOGIN) {
  const router = useRouter();

  useEffect(() => {
    const isAuthenticated = authUtils.isAuthenticated();

    if (!isAuthenticated) {
      router.push(redirectTo);
    }
  }, [router, redirectTo]);
}
