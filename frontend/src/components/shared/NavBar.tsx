import { Link, NavLink } from "react-router-dom";
import { BookOpen, Database, Github, Home, Moon, Settings, Sun, Waves } from "lucide-react";

interface NavBarProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    "h-10 px-3 border border-line bg-white/70 backdrop-blur inline-flex shrink-0 items-center gap-2 text-sm font-bold",
    isActive ? "text-blue border-blue" : "text-ink",
  ].join(" ");

export default function NavBar({ theme, onToggleTheme }: NavBarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-paper/78 backdrop-blur-xl">
      <div className="w-[min(1180px,calc(100%-32px))] mx-auto py-3 flex flex-wrap items-center justify-between gap-3 max-[820px]:w-[min(100%-20px,680px)]">
        <Link to="/" className="min-h-10 border border-ink bg-blue text-white px-3 inline-flex shrink-0 items-center gap-2 font-black no-underline">
          <Home size={16} />
          AutoDerivation
        </Link>

        <nav className="flex flex-wrap gap-2 items-center">
          <NavLink to="/generator" className={navClass}>
            <Database size={15} />
            Generator
          </NavLink>
          <NavLink to="/etymologist" className={navClass}>
            <BookOpen size={15} />
            Etymologist
          </NavLink>
          <NavLink to="/settings" className={navClass}>
            <Settings size={15} />
            Settings
          </NavLink>
          <NavLink to="/dictionary" className={navClass}>
            <BookOpen size={15} />
            Dictionary
          </NavLink>
          <NavLink to="/phonology" className={navClass}>
            <Waves size={15} />
            Phonology
          </NavLink>
        </nav>

        <div className="flex flex-nowrap gap-2 items-center shrink-0">
          <button
            type="button"
            onClick={onToggleTheme}
            className="h-10 px-3 border border-ink bg-white text-ink inline-flex shrink-0 items-center gap-2 font-extrabold"
            title="Toggle theme"
          >
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <a className="h-10 px-3 border border-line bg-white/70 inline-flex shrink-0 items-center gap-2 font-bold text-sm text-ink no-underline" href="https://github.com/" target="_blank" rel="noreferrer">
            <Github size={15} />
            GitHub
          </a>
          <a className="h-10 px-3 border border-line bg-white/70 inline-flex shrink-0 items-center gap-2 font-bold text-sm text-ink no-underline" href="https://github.com/panjo" target="_blank" rel="noreferrer">
            Home
          </a>
        </div>
      </div>
    </header>
  );
}
