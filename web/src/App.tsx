import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BriefPage } from "./pages/BriefPage";
import { ContentIdeasPage } from "./pages/ContentIdeasPage";
import { GenerateBriefPage } from "./pages/GenerateBriefPage";
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
        <Route path="briefs/generate/:reportId" element={<GenerateBriefPage />} />
        <Route path="briefs/:id" element={<BriefPage />} />
        <Route path="ideas/:briefItemId" element={<ContentIdeasPage />} />
        <Route path="settings/prompts" element={<PromptsPage />} />
        <Route path="settings/sources" element={<SourcesPage />} />
        <Route path="reports/:id" element={<ReportPage />} />
      </Route>
    </Routes>
  );
}
