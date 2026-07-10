import { Route, Routes, Navigate, useLocation, useParams } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BriefPage } from "./pages/BriefPage";
import { GenerateBriefPage } from "./pages/GenerateBriefPage";
import { HomePage } from "./pages/HomePage";
import { NewResearchPage } from "./pages/NewResearchPage";
import { PromptsPage } from "./pages/PromptsPage";
import { ReportPage } from "./pages/ReportPage";
import { SourcesPage } from "./pages/SourcesPage";

function IdeasRedirect() {
  const { briefItemId: _briefItemId } = useParams<{ briefItemId: string }>();
  const location = useLocation();
  const briefId = new URLSearchParams(location.search).get("brief");
  if (briefId) {
    return <Navigate to={`/briefs/${briefId}`} replace />;
  }
  return <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="new" element={<NewResearchPage />} />
        <Route path="briefs/generate/:reportId/:trendName" element={<GenerateBriefPage />} />
        <Route path="briefs/:id" element={<BriefPage />} />
        <Route path="ideas/:briefItemId" element={<IdeasRedirect />} />
        <Route path="settings/prompts" element={<PromptsPage />} />
        <Route path="settings/sources" element={<SourcesPage />} />
        <Route path="reports/:id" element={<ReportPage />} />
      </Route>
    </Routes>
  );
}
