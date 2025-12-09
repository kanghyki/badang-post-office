import type { Metadata } from "next";
import "./globals.scss";
import "./globals.module.scss";

export const metadata: Metadata = {
  title: "제주헌디",
  description: "제주방언 살리기 프로젝트",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        {children}
      </body>
    </html>
  );
}
