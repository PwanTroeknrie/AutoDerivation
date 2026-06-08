import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/shared/NavBar";
import HeroPage from "./pages/HeroPage";
import GeneratorPage from "./pages/GeneratorPage";
import EtymologistPage from "./pages/EtymologistPage";
import SettingsPage from "./pages/SettingsPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import { warmupEtymology } from "./api/client";

type Theme = "light" | "dark";
export type WarmupState = "warming" | "ready" | "failed";

function initialTheme(): Theme {
  const stored = localStorage.getItem("autoderivation-theme");
  return stored === "dark" ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [warmupState, setWarmupState] = useState<WarmupState>("warming");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("autoderivation-theme", theme);
  }, [theme]);

  useEffect(() => {
    setWarmupState("warming");
    warmupEtymology(true)
      .then((result) => setWarmupState(result.ok ? "ready" : "failed"))
      .catch(() => setWarmupState("failed"));
  }, []);

  return (
    <BrowserRouter>
      <NavBar
        theme={theme}
        onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      />
      <Routes>
        <Route path="/" element={<HeroPage warmupState={warmupState} />} />
        <Route path="/generator" element={<GeneratorPage />} />
        <Route path="/etymologist" element={<EtymologistPage warmupState={warmupState} />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route
          path="/dictionary"
          element={
            <PlaceholderPage
              title="Dictionary"
              label="Dictionary Project"
              description="词典项目入口已放好。后续可以接入词条浏览、语义标签、派生关系图和批量编辑工作流。"
            />
          }
        />
        <Route
          path="/phonology"
          element={
            <PlaceholderPage
              title="Phonology Executor"
              label="Phonology Project"
              description="音系执行器入口已放好。后续可以接入规则链预览、逐步应用、音变差异对比和调试日志。"
            />
          }
        />
        <Route path="/workspace" element={<Navigate to="/generator" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
