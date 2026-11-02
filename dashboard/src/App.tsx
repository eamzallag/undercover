import { Link, NavLink, Route, Routes } from "react-router";
import { ClaimPage } from "./ClaimPage";
import { InstructionsPage } from "./InstructionsPage";
import { QueuePage } from "./QueuePage";

export function App() {
  return (
    <div className="shell">
      <header className="header">
        <Link className="brand" to="/">
          <span className="brand-name">UnderCover</span>
          <span className="tagline">The claims desk</span>
        </Link>
        <nav className="nav" aria-label="Main">
          <NavLink to="/" end>
            Queue
          </NavLink>
          <NavLink to="/instructions">Instructions</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<QueuePage />} />
        <Route path="/claims/:claimId" element={<ClaimPage />} />
        <Route path="/instructions" element={<InstructionsPage />} />
        <Route
          path="*"
          element={
            <main className="page">
              <h1>Page not found</h1>
            </main>
          }
        />
      </Routes>
    </div>
  );
}
