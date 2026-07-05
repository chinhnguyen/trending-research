import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { NewResearchPage } from "./pages/NewResearchPage";
import { PromptsPage } from "./pages/PromptsPage";
import { ReportPage } from "./pages/ReportPage";
import { SourcesPage } from "./pages/SourcesPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="new" element={<NewResearchPage />} />
        <Route path="settings/prompts" element={<PromptsPage />} />
        <Route path="settings/sources" element={<SourcesPage />} />
        <Route path="reports/:id" element={<ReportPage />} />
      </Route>
    </Routes>
  );
}
