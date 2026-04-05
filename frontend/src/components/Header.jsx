export default function Header() {
  return (
    <header style={{
      borderBottom: "1px solid #2A2A2A",
      padding: "16px 0",
      marginBottom: "32px",
    }}>
      <div className="container flex items-center justify-between">
        <div>
          <span style={{ fontSize: 22, fontWeight: 700, color: "var(--gold)" }}>
            সোনার দাম
          </span>
          <span style={{ fontSize: 13, color: "var(--text-muted)", marginLeft: 10 }}>
            BAJUS অনুযায়ী
          </span>
        </div>
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
          বাংলাদেশ জুয়েলার্স সমিতি
        </span>
      </div>
    </header>
  );
}
