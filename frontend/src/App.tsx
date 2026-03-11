import { Routes, Route, Navigate } from 'react-router-dom';
import { ChatView } from './components/chat/ChatView';
import { KnowledgePage } from './components/knowledge/KnowledgePage';
import { SessionDetailPage } from './components/sessions/SessionDetailPage';
import { Navigation } from './components/layout/Navigation';
import { ToastContainer } from './components/ui/Alert';
import { AntdProvider } from './components/common/AntdProvider';
import { LoginForm } from './components/auth/LoginForm';
import { useNavigate } from 'react-router-dom';

// Login page wrapper that handles navigation after login
function LoginPage() {
  const navigate = useNavigate();

  const handleSuccess = () => {
    navigate('/');
  };

  return <LoginForm onSuccess={handleSuccess} />;
}

function App() {
  return (
    <AntdProvider>
      <div className="App">
        <Routes>
          {/* Login page without navigation */}
          <Route path="/login" element={<LoginPage />} />

          {/* Main app with navigation */}
          <Route
            path="/*"
            element={
              <>
                <Navigation />
                <Routes>
                  <Route path="/" element={<ChatView />} />
                  <Route path="/chat" element={<ChatView />} />
                  <Route path="/chat/:sessionId" element={<SessionDetailPage />} />
                  <Route path="/knowledge" element={<KnowledgePage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                <ToastContainer />
              </>
            }
          />
        </Routes>
      </div>
    </AntdProvider>
  );
}

export default App;
