import Link from "next/link";
import Header from "../Components/Header";
import PostcardItem from "../Components/PostcardItem";
import styles from "./list.module.scss";


export default function List() {
  const pageTitle = "예약엽서 목록";
  

  // 실제로는 API fetch로 받아올 데이터
  const postcards = [
    {
      id: "post_1",
      title: "Happy New Year!",
      origin_content: "안녕하세요. 새해 복 많이 받으세요.",
      jeju_content: "안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예.",
      to_email: "test1@example.com",
      scheduled_delivery_date: "2026-12-25T09:00:00Z",
      created_at: "2025-12-09T10:00:00Z"
    },
    {
      id: "post_2",
      title: "Merry Christmas",
      origin_content: "메리 크리스마스!",
      jeju_content: "메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과!",
      to_email: "test2@example.com",
      scheduled_delivery_date: "2027-12-20T09:00:00Z",
      created_at: "2025-12-08T08:30:00Z"
    },
    {
      id: "post_3",
      title: "Happy New Year!",
      origin_content: "안녕하세요. 새해 복 많이 받으세요.",
      jeju_content: "안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예.",
      to_email: "test1@example.com",
      scheduled_delivery_date: "2024-12-25T09:00:00Z",
      created_at: "2025-12-07T10:00:00Z"
    },
    {
      id: "post_4",
      title: "Merry Christmas",
      origin_content: "메리 크리스마스!",
      jeju_content: "메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과!",
      to_email: "test2@example.com",
      scheduled_delivery_date: "2024-12-20T09:00:00Z",
      created_at: "2025-11-01T08:30:00Z"
    },
    {
      id: "post_5",
      title: "Happy New Year!",
      origin_content: "안녕하세요. 새해 복 많이 받으세요.",
      jeju_content: "안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예. 안녕하우꽈. 새해 복 많이 받으서예.",
      to_email: "test1@example.com",
      scheduled_delivery_date: "2024-12-25T09:00:00Z",
      created_at: "2024-12-01T10:00:00Z"
    },
    {
      id: "post_6",
      title: "Merry Christmas",
      origin_content: "메리 크리스마스!",
      jeju_content: "메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과! 메리 크리스마스 하수과!",
      to_email: "test2@example.com",
      scheduled_delivery_date: "2024-12-20T09:00:00Z",
      created_at: "2023-11-30T08:30:00Z"
    }
  ];

  return (
    <>
      <div className="hdWrap">
        <Header title="예약엽서목록" path="/user"/>
      </div>

      <div className="container">
        <div className={styles.postCopy}>
          오늘도 해 넘어가는 들녘<br/>바라보멍 너 생각에 웃음 나불어<br/>이 정 담은 편지를 살그마니 보낸다게
        </div>
        <main className={styles.listMain}>
          <div className={styles.postcardBox}>
            {postcards.map((item) => (
              <PostcardItem key={item.id} data={item} />
            ))}
          </div>
        </main>
      </div>
      <div className="navWrap">
        <Link href="/write" className={"btnBig"} style={{color: "#FFF"}}>
          엽서 작성하기
        </Link>
      </div>
    </>
  );
}