import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./lib/auth-context";
import ErrorBoundary from "./lib/ErrorBoundary";
import Sidebar from "./components/ui/Sidebar";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import UnifiedDashboardPage from "./pages/UnifiedDashboardPage";
import DashboardPage from "./pages/DashboardPage";
import LinkedInSourcingPage from "./pages/LinkedInSourcingPage";
import AllLeadsPage from "./pages/AllLeadsPage";
import LeadDetailPage from "./pages/LeadDetailPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import EmailPage from "./pages/EmailPage";
import EmailMonitoringPage from "./pages/EmailMonitoringPage";
import CampaignDetailPage from "./pages/CampaignDetailPage";
import SettingsPage from "./pages/SettingsPage";
import ChatbotPage from "./pages/ChatbotPage";
import PipelinePage from "./pages/PipelinePage";

function ProtectedLayout({ children }) {
  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}

export default function App() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-400">
        Loading...
      </div>
    );
  }

  return (
    <ErrorBoundary>
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />}
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <UnifiedDashboardPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/dashboard"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <DashboardPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/linkedin"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <LinkedInSourcingPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/campus"
        element={<Navigate to="/linkedin" replace />}
      />
      <Route
        path="/leads"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <AllLeadsPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/leads/:id"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <LeadDetailPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/analytics"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <AnalyticsPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/email"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <EmailPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/email/:id"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <CampaignDetailPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/email-monitoring"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <EmailMonitoringPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/settings"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <SettingsPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/chatbot"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <ChatbotPage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/pipeline"
        element={
          isAuthenticated ? (
            <ProtectedLayout>
              <PipelinePage />
            </ProtectedLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </ErrorBoundary>
  );
}
