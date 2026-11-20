import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ToastProvider, useToast } from '@/components/ui/Toast';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { LanguageProvider } from '@/context/LanguageContext';
import { Navbar } from '@/components/Navbar';
import { Hero } from '@/components/Hero';
import { ExplainerSteps } from '@/components/ExplainerSteps';
import { DesignSystemShowcase } from '@/components/DesignSystemShowcase';
import { SafetyContractSection } from '@/components/SafetyContractSection';
import { Footer } from '@/components/Footer';
import { DocumentUploadModal } from '@/components/documents/DocumentUploadModal';
import { DocumentVaultModal } from '@/components/documents/DocumentVaultModal';
import { DocumentWorkspace } from '@/components/documents/DocumentWorkspace';
import { LoginPage } from '@/pages/LoginPage';
import { SignupPage } from '@/pages/SignupPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ChatDashboardPage } from '@/pages/ChatDashboardPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { LegalAssistantChat } from '@/components/chat/LegalAssistantChat';

// Initialize TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 10,
      refetchOnWindowFocus: false,
    },
  },
});

type ViewState = 'landing' | 'dashboard' | 'login' | 'signup' | 'settings' | 'chat';

function MainLayout() {
  const { user, logout, isLoading } = useAuth();
  const { addToast } = useToast();

  // Theme state: dark or light mode
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('law-mithra-theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Modal & Workspace state
  const [currentView, setCurrentView] = useState<ViewState>('landing');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isVaultModalOpen, setIsVaultModalOpen] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('law-mithra-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('law-mithra-theme', 'light');
    }
  }, [darkMode]);

  // When user logs in, if they were on landing or auth pages, send them to dashboard
  useEffect(() => {
    if (user && (currentView === 'login' || currentView === 'signup')) {
      setCurrentView('dashboard');
    }
  }, [user, currentView]);

  // Protected route enforcement
  const handleNavigate = (view: ViewState) => {
    setSelectedDocumentId(null);
    if ((view === 'dashboard' || view === 'settings' || view === 'chat') && !user) {
      addToast({
        title: 'Sign In Required',
        description: 'Please log in to access Law Mithra dashboard and legal assistant.',
        variant: 'info',
      });
      setCurrentView('login');
      return;
    }
    setCurrentView(view);
  };

  const handleOpenUpload = () => {
    if (!user) {
      addToast({
        title: 'Sign In Required',
        description: 'Please sign in or create an account to upload documents to your vault.',
        variant: 'info',
      });
      setCurrentView('login');
      return;
    }
    setIsUploadModalOpen(true);
  };

  const handleOpenVault = () => {
    if (!user) {
      addToast({
        title: 'Sign In Required',
        description: 'Please sign in to access your private document vault.',
        variant: 'info',
      });
      setCurrentView('login');
      return;
    }
    setIsVaultModalOpen(true);
  };

  // When on pure landing page, render only the full-screen 100vw x 100vh hero
  if (currentView === 'landing' && !selectedDocumentId) {
    return (
      <Hero
        onLoginClick={() => setCurrentView(user ? 'dashboard' : 'login')}
        isLoggedIn={!!user}
      />
    );
  }

  // When on pure login page, render the full-screen 100vw x 100vh premium dark login
  if (currentView === 'login' && !selectedDocumentId) {
    return (
      <LoginPage
        onNavigateSignup={() => setCurrentView('signup')}
        onLoginSuccess={() => setCurrentView('dashboard')}
        onNavigateHome={() => setCurrentView('landing')}
      />
    );
  }

  // When on pure signup page, render the full-screen 100vw x 100vh premium dark signup
  if (currentView === 'signup' && !selectedDocumentId) {
    return (
      <SignupPage
        onNavigateLogin={() => setCurrentView('login')}
        onSignupSuccess={() => setCurrentView('dashboard')}
        onNavigateHome={() => setCurrentView('landing')}
      />
    );
  }

  // Protected: When on chat view, render the dedicated ChatDashboardPage
  if (currentView === 'chat' && !selectedDocumentId) {
    if (!user) {
      return (
        <Hero
          onLoginClick={() => setCurrentView('login')}
          isLoggedIn={false}
        />
      );
    }

    const handleDashboardLogout = async () => {
      try {
        await logout();
      } catch (err) {
        console.error('Logout error:', err);
      }
      setCurrentView('landing');
    };

    return (
      <>
        <ChatDashboardPage
          onOpenUpload={handleOpenUpload}
          onOpenVault={handleOpenVault}
          onOpenDashboard={() => setCurrentView('dashboard')}
          onNavigateHome={() => setCurrentView('landing')}
          onOpenSettings={() => setCurrentView('settings')}
          onLogout={handleDashboardLogout}
        />
        {/* Modals for Document Upload & Vault */}
        <DocumentUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUploadSuccess={(doc) => {
            setSelectedDocumentId(doc.id);
          }}
        />
        <DocumentVaultModal
          isOpen={isVaultModalOpen}
          onClose={() => setIsVaultModalOpen(false)}
          onSelectDocument={(id) => setSelectedDocumentId(id)}
          onOpenUpload={handleOpenUpload}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-ivory dark:bg-charcoal text-slate-800 dark:text-slate-100 selection:bg-gold-200 selection:text-navy-900 transition-colors duration-200">
      <Navbar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        currentView={currentView}
        onNavigate={handleNavigate}
        onOpenUpload={handleOpenUpload}
        onOpenVault={handleOpenVault}
      />

      <main className="flex-1">
        {selectedDocumentId ? (
          <DocumentWorkspace
            documentId={selectedDocumentId}
            onBack={() => {
              setSelectedDocumentId(null);
              setCurrentView(user ? 'dashboard' : 'landing');
            }}
            onDocumentDeleted={() => {
              setSelectedDocumentId(null);
              setCurrentView('dashboard');
            }}
          />
        ) : currentView === 'login' ? (
          <LoginPage
            onNavigateSignup={() => setCurrentView('signup')}
            onLoginSuccess={() => setCurrentView('dashboard')}
          />
        ) : currentView === 'signup' ? (
          <SignupPage
            onNavigateLogin={() => setCurrentView('login')}
            onSignupSuccess={() => setCurrentView('dashboard')}
          />
        ) : currentView === 'chat' ? (
          <div className="max-w-5xl mx-auto px-4 py-8">
            <LegalAssistantChat standalone={true} />
          </div>
        ) : currentView === 'dashboard' && user ? (
          <DashboardPage
            onOpenUpload={handleOpenUpload}
            onSelectDocument={(id) => setSelectedDocumentId(id)}
          />
        ) : currentView === 'settings' && user ? (
          <SettingsPage onBack={() => setCurrentView('dashboard')} />
        ) : (
          <Hero
            onLoginClick={() => setCurrentView(user ? 'dashboard' : 'login')}
            isLoggedIn={!!user}
          />
        )}
      </main>

      <Footer />

      {/* Modals */}
      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={(doc) => {
          setSelectedDocumentId(doc.id);
        }}
      />

      <DocumentVaultModal
        isOpen={isVaultModalOpen}
        onClose={() => setIsVaultModalOpen(false)}
        onSelectDocument={(id) => setSelectedDocumentId(id)}
        onOpenUpload={handleOpenUpload}
      />
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastProvider>
          <AuthProvider>
            <LanguageProvider>
              <MainLayout />
            </LanguageProvider>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
