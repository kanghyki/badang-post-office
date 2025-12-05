import Image from "next/image";

export default function Home() {
  return (
    <div className="">
      <header className="header">
        <h1>LIST</h1>
      </header>
      <main className="">
        <div className="listBox">
          <div className="listItem">
            <div className="writeDate"><p>2025-01-01</p></div>
            <div>
              <p className="recipient"><b>To.</b><span>{"loewy.moon@gmail.com"}</span></p>
              <p className="reservationDate"><span>{"2026.12.01"}</span><b>보내기</b></p>
            </div>
            <div className="title"><p>Title</p></div>
            <div className="content"><p>Content</p></div>
          </div>
          <div className="itemSetting">
            <div className="itemSettingBtn"><p>수정</p></div>
            <div className="itemSettingBtn"><p>삭제</p></div>
          </div>
        </div>
        <div className="listBox">
          <div className="listItem">
            <div className="writeDate"><p>2025-01-01</p></div>
            <div>
              <p className="recipient"><b>To.</b><span>{"loewy.moon@gmail.com"}</span></p>
              <p className="reservationDate"><span>{"2026.12.01"}</span><b>보내기</b></p>
            </div>
            <div className="title"><p>Title</p></div>
            <div className="content"><p>Content</p></div>
          </div>
          <div className="itemSetting">
            <div className="itemSettingBtn"><p>수정</p></div>
            <div className="itemSettingBtn"><p>삭제</p></div>
          </div>
        </div>
      </main>
    </div>
  );
}