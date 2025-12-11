import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { authUtils } from "@/lib/utils/auth";

export function useAuth(redirectTo: string = "/login") {
  const router = useRouter();

  useEffect(() => {
    const isAuthenticated = authUtils.isAuthenticated();

    if (!isAuthenticated) {
      router.push(redirectTo);
    }
  }, [router, redirectTo]);
}
