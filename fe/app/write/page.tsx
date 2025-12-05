import Image from "next/image";

export default function Home() {
  return (
    <div className="">
      <header className="header">
        <h1>WRITE</h1>
      </header>
      <main className="">
        <form action="">
          <input type="text" placeholder="Title" />
          <textarea placeholder="Content" />
          
          <input type="email" placeholder="Email" />
          <input type="date" placeholder="Date" />
          <button type="submit">SAVE</button>
        </form>
      </main>
    </div>
  );
}