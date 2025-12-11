import type { Metadata } from "next";
import "@/styles/globals.scss";
import "@/styles/globals.module.scss";
import { StoreProvider } from "@/store/StoreProvider";
import { NotificationProvider } from "./context/NotificationContext";
import ConditionalFooter from "./components/ConditionalFooter";

export const metadata: Metadata = {
  title: "바당우체국",
  description: "제주바당우체국",
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
