import type { Metadata, Viewport } from "next";
import "@/styles/globals.scss";
import "@/styles/globals.module.scss";
import { StoreProvider } from "@/store/StoreProvider";
import { NotificationProvider } from "./context/NotificationContext";
import ConditionalFooter from "./components/ConditionalFooter";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#ffefef", // 대부분 페이지의 배경색
};

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"
  ),
  title: {
    default: "바당우체국",
    template: "%s | 바당우체국",
  },
  description:
    "제주 방언으로 따뜻한 마음을 전하는 디지털 엽서 서비스. 제주의 정취를 담아 소중한 사람에게 엽서를 보내보세요.",
  keywords: [
    "제주",
    "엽서",
    "우체국",
    "바당",
    "제주 방언",
    "디지털 엽서",
    "추억",
    "감성",
    "제주어",
  ],
  authors: [{ name: "바당우체국" }],
  creator: "바당우체국",
  publisher: "바당우체국",

  openGraph: {
    title: "바당우체국",
    description: "제주 방언으로 따뜻한 마음을 전하는 디지털 엽서 서비스",
    url: process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000",
    siteName: "바당우체국",
    locale: "ko_KR",
    type: "website",
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "바당우체국 - 제주 방언으로 따뜻한 마음을 전하는 디지털 엽서 서비스",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    title: "바당우체국",
    description: "제주 방언으로 따뜻한 마음을 전하는 디지털 엽서 서비스",
    images: ["/opengraph-image.png"],
  },

  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },

  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },

  verification: {
    google: "your-google-verification-code",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}
      >
        <StoreProvider>
          <NotificationProvider>
            <div style={{ flex: 1 }}>{children}</div>
            <ConditionalFooter />
          </NotificationProvider>
        </StoreProvider>
      </body>
    </html>
  );
}
