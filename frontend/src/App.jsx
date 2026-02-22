import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import EvaluationPage from './pages/EvaluationPage';
import SettingsPage from './pages/SettingsPage';

const pages = {
  chat: ChatPage,
  documents: DocumentsPage,
  analytics: AnalyticsPage,
  evaluation: EvaluationPage,
  settings: SettingsPage,
};

export default function App() {
  const [activePage, setActivePage] = useState('chat');
  const ActivePage = pages[activePage];

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onPageChange={setActivePage} />
      <main className="main-content">
        <ActivePage />
      </main>
    </div>
  );
}
