import type { Viewport } from "next";

export const viewport: Viewport = {
  themeColor: "#FE6716", // 시작 페이지의 배경색
};

export default function RootPageLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
