import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Header, Footer } from './components';
import {
  NationalMapSearch,
  LocalityDossier,
  ProjectDetail,
  ContractorDossier,
  CompareLocalities,
  MethodologyEvidence,
} from './pages';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-surface text-on-surface">
      <Header />
      <main className="flex-1 w-full pt-16 md:pt-24 bg-surface">
        <Routes>
          <Route path="/" element={<NationalMapSearch />} />
          <Route path="/locality/:psgcCode" element={<LocalityDossier />} />
          <Route path="/project/:contractId" element={<ProjectDetail />} />
          <Route path="/contractor/:id" element={<ContractorDossier />} />
          <Route path="/compare" element={<CompareLocalities />} />
          <Route path="/methodology" element={<MethodologyEvidence />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
};

export default App;
