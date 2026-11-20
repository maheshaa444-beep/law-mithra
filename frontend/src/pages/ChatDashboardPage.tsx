import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Scale,
  Plus,
  Search,
  MessageSquare,
  Settings,
  Globe2,
  ChevronDown,
  Paperclip,
  Mic,
  Send,
  PanelLeftClose,
  PanelLeft,
  X,
  FileText,
  Upload,
  FolderLock,
  Copy,
  Check,
  Sparkles,
  Trash2,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { useToast } from '@/components/ui/Toast';
import { SupportedLanguage } from '@/lib/translations';
import {
  askLegalAssistant,
  fetchChatSessions,
  fetchChatSessionDetail,
  createChatSession,
  deleteChatSession,
} from '@/lib/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  statutes?: string[];
  timestamp: string;
}

function cleanFormatting(text: string): string {
  if (!text) return '';
  return text
    .replace(/#{1,6}\s*/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/^\s*[\*\-]\s+/gm, '• ')
    .replace(/\[([^\]]+)\]/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
}

interface ChatDashboardPageProps {
  onOpenUpload?: () => void;
  onOpenVault?: () => void;
  onOpenSettings?: () => void;
  onOpenDashboard?: () => void;
  onNavigateHome?: () => void;
  onLogout?: () => void;
}

export function ChatDashboardPage({
  onOpenUpload,
  onOpenVault,
  onOpenSettings,
  onOpenDashboard,
  onNavigateHome,
  onLogout,
}: ChatDashboardPageProps) {
  const { user, logout } = useAuth();
  const { addToast } = useToast();
  const { language, setLanguage, languages, t, currentLanguage } = useLanguage();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [languageDropdownOpen, setLanguageDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [attachMenuOpen, setAttachMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [recentChats, setRecentChats] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  // Persistence, loading and deletion state
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [deleteConfirmSessionId, setDeleteConfirmSessionId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Load persistent conversation sessions on mount and user auth change
  const loadSessions = useCallback(async (selectId?: string | null) => {
    setSessionsLoading(true);
    setSessionError(null);
    try {
      const serverSessions = await fetchChatSessions();
      const mapped: ChatSession[] = serverSessions.map((s) => ({
        id: s.id,
        title: s.title,
        messages: [],
      }));
      setRecentChats(mapped);

      const targetId = selectId !== undefined ? selectId : (mapped.length > 0 ? mapped[0].id : null);
      if (targetId) {
        const target = mapped.find((s) => s.id === targetId) || mapped[0];
        if (target) {
          await loadSessionDetail(target.id);
        }
      }
    } catch (err: any) {
      setSessionError(err.message || 'Failed to load conversation history.');
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [user, loadSessions]);

  // Load message thread for a selected session
  const loadSessionDetail = async (sessionId: string) => {
    setActiveChatId(sessionId);
    try {
      const detail = await fetchChatSessionDetail(sessionId);
      const mappedMsgs: ChatMessage[] = detail.messages.map((m) => {
        const statutes = (m.statutory_citations || []).flatMap((s: any) =>
          (s.sections || []).map((sec: string) => `${sec} (${s.act})`)
        );
        return {
          id: m.id,
          sender: m.sender,
          text: m.content,
          statutes,
          timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      });
      setMessages(mappedMsgs);
    } catch (err) {
      console.error('Failed to load session detail', err);
    }
  };

  // Handle new chat click
  const handleNewChat = () => {
    setMessages([]);
    setActiveChatId(null);
    setInputMessage('');
    if (inputRef.current) inputRef.current.focus();
  };

  // Sign out handler that properly triggers logout and redirects
  const handleSignOut = async () => {
    setUserDropdownOpen(false);
    try {
      await logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    if (onLogout) {
      onLogout();
    }
  };

  // Select a recent chat session
  const handleSelectSession = (session: ChatSession) => {
    loadSessionDetail(session.id);
  };

  // Delete a specific conversation session
  const handleDeleteSession = async (sessionId: string) => {
    setIsDeleting(true);
    try {
      await deleteChatSession(sessionId);
      setRecentChats((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeChatId === sessionId) {
        handleNewChat();
      }
      setDeleteConfirmSessionId(null);
    } catch (err) {
      console.error('Failed to delete session', err);
    } finally {
      setIsDeleting(false);
    }
  };

  // Send message
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || isThinking) return;

    const userMsg: ChatMessage = {
      id: 'user-' + Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsThinking(true);

    try {
      const clientReqId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : undefined;
      const res = await askLegalAssistant(query, language, true, activeChatId, clientReqId);

      const assistantMsg: ChatMessage = {
        id: res.assistant_message_id || 'assistant-' + Date.now(),
        sender: 'assistant',
        text: res.explanation || res.legal_issue || res.advice || 'Statutory remedies retrieved.',
        statutes: res.statutory_references || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // If backend created or returned a session_id, sync it
      if (res.session_id) {
        setActiveChatId(res.session_id);
      }

      // Refresh session list to reflect new/updated conversation
      const serverSessions = await fetchChatSessions().catch(() => null);
      if (serverSessions) {
        setRecentChats(
          serverSessions.map((s) => ({
            id: s.id,
            title: s.title,
            messages: [],
          }))
        );
      }
    } catch (err: any) {
      addToast({
        title: 'Legal AI Notice',
        description: err.message || 'Network error communicating with AI. Providing statutory reference guidance.',
        variant: 'warning',
      });
      // High-precision fallback response in selected language
      const fallbackMsg: ChatMessage = {
        id: 'assistant-' + Date.now(),
        sender: 'assistant',
        text:
          language === 'kn'
            ? `ನಿಮ್ಮ ಪ್ರಶ್ನೆ: "${query}". ಭಾರತೀಯ ಕಾನೂನಿನಡಿ, ಪರಿಹಾರಗಳು ಸಿವಿಲ್ ಅಥವಾ ಕ್ರಿಮಿನಲ್ ಸ್ವರೂಪವನ್ನು ಅವಲಂಬಿಸಿವೆ. ಜಮೀನು ಒತ್ತುವರಿ ಅಥವಾ ಸ್ವಾಧೀನದ ವಿವಾದಗಳಿಗೆ ನಿರ್ದಿಷ್ಟ ಪರಿಹಾರ ಕಾಯ್ದೆ (Specific Relief Act) ಕಲಂ 6 ಮತ್ತು CPC ಆರ್ಡರ್ 39 ನಿಯಮಗಳು 1 ಮತ್ತು 2 ರ ಅಡಿಯಲ್ಲಿ ಪರಿಹಾರಗಳಿವೆ. ಅಪರಾಧಗಳಿಗೆ ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ (BNS) / IPC ಮತ್ತು BNSS / CrPC ಅಡಿಯಲ್ಲಿ ರಕ್ಷಣೆ ದೊರೆಯುತ್ತದೆ.`
            : language === 'hi'
            ? `आपका प्रश्न: "${query}". भारतीय कानूनी संहिता के तहत, उपाय इस बात पर निर्भर करते हैं कि मामला दीवानी (Civil) है या आपराधिक (Criminal)। भूमि विवाद या बेदखली के मामलों में विशिष्ट राहत अधिनियम (Specific Relief Act) की धारा 6 और CPC के आदेश 39 नियम 1 व 2 के तहत उपाय उपलब्ध हैं।`
            : language === 'ta'
            ? `உங்கள் கேள்வி: "${query}". இந்திய சட்டத்தின்படி, தீர்வுகள் உரிமையியல் அல்லது குற்றவியல் தன்மையைப் பொறுத்தது. நில ஆக்கிரமிப்பு விவகாரங்களில் Specific Relief Act பிரிவு 6 மற்றும் CPC Order 39 விதிகள் 1 & 2-ன் கீழ் தீர்வுகள் உள்ளன.`
            : language === 'te'
            ? `మీ ప్రశ్న: "${query}". భారతీయ చట్టాల ప్రకారం, పరిష్కారాలు సివిల్ లేదా క్రిమినల్ స్వభావంపై ఆధారపడి ఉంటాయి. భూ వివాదాలలో Specific Relief Act సెక్షన్ 6 మరియు CPC Order 39 రూల్స్ 1 & 2 కింద తక్షణ ఉపశమనం లభిస్తుంది.`
            : `Regarding: "${query}". Under Indian statutory law, civil dispossession remedies lie under Section 6 of the Specific Relief Act, 1963 and Order 39 Rules 1 & 2 CPC. Criminal offences are actionable under Bharatiya Nyaya Sanhita (BNS) / IPC and BNSS / CrPC.`,
        statutes: [
          'Specific Relief Act, 1963 (Section 6)',
          'Code of Civil Procedure, 1908 (Order 39 Rules 1 & 2)',
          'Bharatiya Nagarik Suraksha Sanhita (BNSS)',
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleVoiceToggle = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = language === 'en' ? 'en-IN' : language;
    recognition.interimResults = false;

    if (!isListening) {
      setIsListening(true);
      recognition.start();
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
    } else {
      setIsListening(false);
    }
  };

  // Filtered recent chats based on user's actual sessions
  const filteredChats = recentChats.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const currentLangObj = languages.find((l) => l.code === language) || languages[0];
  const userDisplayName = user?.email?.split('@')[0] || 'User';
  const userInitial = userDisplayName.charAt(0).toUpperCase() || 'U';

  return (
    <div
      className={`relative w-screen h-screen overflow-hidden bg-[#050505] text-[#EDEDED] flex select-none ${
        currentLanguage?.fontClass || 'font-sans'
      }`}
      style={{
        background: 'radial-gradient(circle at 50% 50%, #0A0A0A 0%, #070707 60%, #050505 100%)',
      }}
    >
      {/* Background Subtle Texture */}
      <svg className="pointer-events-none fixed inset-0 w-full h-full opacity-[0.035] z-[1]">
        <filter id="noiseFilterDashboard">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noiseFilterDashboard)" />
      </svg>

      {/* Vignette */}
      <div
        className="pointer-events-none absolute inset-0 z-[2]"
        style={{
          background:
            'radial-gradient(ellipse at 50% 50%, transparent 45%, rgba(0, 0, 0, 0.7) 85%, rgba(0, 0, 0, 0.95) 100%)',
        }}
      />

      {/* Reusable SVG Gradients and Filters */}
      <svg className="absolute w-0 h-0" aria-hidden="true">
        <defs>
          <linearGradient id="goldGradientDash" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F7DE9B" />
            <stop offset="45%" stopColor="#D9A441" />
            <stop offset="80%" stopColor="#A8731F" />
            <stop offset="100%" stopColor="#6B4410" />
          </linearGradient>

          <filter id="goldGlowDash" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="intenseGlowDash" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="b2" />
            <feMerge>
              <feMergeNode in="b2" />
              <feMergeNode in="b1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>

      {/* =========================================================================
          LEFT SIDEBAR (Width: ~20% / 325px, background #070707, 1px right border)
          ========================================================================= */}
      <aside
        className={`relative z-30 h-full shrink-0 bg-[#070707] border-r border-[#D9A441]/[0.18] flex flex-col transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? 'w-[72px]' : 'w-[325px] max-w-[22vw]'
        } hidden md:flex`}
      >
        {/* 1. Header Row */}
        <div className="h-[76px] px-5 flex items-center justify-between border-b border-white/[0.04]">
          {!sidebarCollapsed ? (
            <div
              onClick={() => {
                if (onOpenDashboard) onOpenDashboard();
                else if (onNavigateHome) onNavigateHome();
              }}
              className="flex items-center gap-3 min-w-0 cursor-pointer group"
              title="Return to Dashboard"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#D9A441]/20 to-[#6B4410]/20 border border-[#D9A441]/40 flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(217,164,65,0.2)] group-hover:border-[#F7DE9B] transition-colors">
                <Scale className="w-4 h-4 text-[#F7DE9B]" />
              </div>
              <div className="truncate">
                <div className="font-serif font-bold text-[24px] leading-tight flex items-baseline">
                  <span className="text-[#F5EEDC] group-hover:text-white transition-colors">{t('hero.titleLaw', 'Law')}</span>
                  <span className="ml-1.5 bg-gradient-to-r from-[#F7DE9B] via-[#D9A441] to-[#A8731F] bg-clip-text text-transparent">
                    {t('hero.titleMithra', 'Mithra')}
                  </span>
                </div>
                <p className="text-[10px] text-[#A69B89] font-sans tracking-wide leading-none mt-0.5">
                  {t('brand.tagline', 'Your Smart Legal Assistant')}
                </p>
              </div>
            </div>
          ) : (
            <div
              onClick={() => {
                if (onOpenDashboard) onOpenDashboard();
                else if (onNavigateHome) onNavigateHome();
              }}
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#D9A441]/20 to-[#6B4410]/20 border border-[#D9A441]/40 flex items-center justify-center mx-auto shadow-[0_0_12px_rgba(217,164,65,0.2)] cursor-pointer hover:border-[#F7DE9B] transition-colors"
              title="Return to Dashboard"
            >
              <Scale className="w-4 h-4 text-[#F7DE9B]" />
            </div>
          )}

          {/* Sidebar Toggle Icon */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1.5 rounded-lg text-[#8A8A8A] hover:text-white hover:bg-white/[0.04] transition-colors"
            title={
              sidebarCollapsed
                ? t('chatDashboard.expandSidebar', 'Expand Sidebar')
                : t('chatDashboard.collapseSidebar', 'Collapse Sidebar')
            }
          >
            {sidebarCollapsed ? <PanelLeft className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </button>
        </div>

        {/* 2. New Chat Button */}
        <div className="px-4 pt-5 pb-3">
          <button
            onClick={handleNewChat}
            className={`w-full h-[50px] rounded-[14px] bg-gradient-to-r from-[#5C4420] via-[#8A6A2E] to-[#4A3618] border border-[#D9A441] shadow-[0_0_20px_rgba(217,164,65,0.22),inset_0_1px_1px_rgba(255,255,255,0.3)] hover:shadow-[0_0_28px_rgba(217,164,65,0.45)] hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center ${
              sidebarCollapsed ? 'justify-center px-0' : 'justify-start px-4 gap-4'
            } group`}
            title={t('chatDashboard.newChat', 'New Chat')}
          >
            <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center shrink-0">
              <Plus className="w-4 h-4 text-white stroke-[2.5]" />
            </div>
            {!sidebarCollapsed && (
              <span className="text-white text-[17px] font-medium tracking-wide">
                {t('chatDashboard.newChat', 'New Chat')}
              </span>
            )}
          </button>
        </div>

        {/* 3. Search Chats Row */}
        {!sidebarCollapsed && (
          <div className="px-4 py-2">
            {isSearching ? (
              <div className="h-[40px] px-3 rounded-xl bg-[#111] border border-[#D9A441]/40 flex items-center gap-2">
                <Search className="w-4 h-4 text-[#D9A441] shrink-0" />
                <input
                  type="text"
                  autoFocus
                  placeholder={t('chatDashboard.filterPlaceholder', 'Filter chats...')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-transparent text-sm text-white placeholder-[#7A7A7A] outline-none font-sans"
                />
                <button
                  onClick={() => {
                    setIsSearching(false);
                    setSearchQuery('');
                  }}
                  className="text-white/40 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsSearching(true)}
                className="w-full h-[40px] px-3 rounded-xl flex items-center gap-3.5 text-white/90 hover:text-white hover:bg-white/[0.04] transition-colors"
              >
                <Search className="w-[18px] h-[18px] text-white/80" />
                <span className="text-[16px] font-normal">
                  {t('chatDashboard.searchChats', 'Search Chats')}
                </span>
              </button>
            )}
          </div>
        )}

        {/* 4. Thin Horizontal Divider */}
        {!sidebarCollapsed && <div className="mx-4 my-2 h-[1px] bg-white/[0.08]" />}

        {/* 5 & 6. Recent Chats List (Scrollable, Clean user sessions only) */}
        <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1.5 scrollbar-thin scrollbar-thumb-white/10">
          {!sidebarCollapsed && (
            <div className="flex items-center justify-between px-3 pt-2 pb-1">
              <p className="text-[13px] font-medium text-[#8A8A8A] tracking-wider uppercase">
                {t('chatDashboard.recentChats', 'Recent Chats')}
              </p>
              {sessionsLoading && <Loader2 className="w-3.5 h-3.5 text-[#D9A441] animate-spin" />}
            </div>
          )}

          {sessionsLoading && filteredChats.length === 0 ? (
            !sidebarCollapsed && (
              <p className="px-3 py-4 text-xs text-[#8A8A8A]/70 flex items-center gap-2 font-sans">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#D9A441]" />
                Loading conversations...
              </p>
            )
          ) : sessionError && filteredChats.length === 0 ? (
            !sidebarCollapsed && (
              <div className="px-3 py-3 text-xs text-red-400 font-sans">
                <p>{sessionError}</p>
                <button onClick={() => loadSessions()} className="mt-1 text-[#D9A441] underline">Retry</button>
              </div>
            )
          ) : filteredChats.length === 0 ? (
            !sidebarCollapsed && (
              <p className="px-3 py-4 text-xs text-[#8A8A8A]/50 italic font-sans">
                {t('chatDashboard.noRecentChats', 'No recent chats')}
              </p>
            )
          ) : (
            filteredChats.map((session) => {
              const isActive = activeChatId === session.id;
              return (
                <div
                  key={session.id}
                  className={`w-full h-[44px] px-3 rounded-xl flex items-center justify-between transition-all group ${
                    isActive
                      ? 'bg-[#D9A441]/10 text-white border-l-2 border-[#D9A441]'
                      : 'text-white/80 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  <button
                    onClick={() => handleSelectSession(session)}
                    className="flex items-center gap-3.5 min-w-0 flex-1 text-left"
                    title={session.title}
                  >
                    <MessageSquare
                      className={`w-[17px] h-[17px] shrink-0 ${
                        isActive ? 'text-[#D9A441]' : 'text-white/70 group-hover:text-white'
                      }`}
                    />
                    {!sidebarCollapsed && (
                      <span className="text-[15px] truncate font-normal">{session.title}</span>
                    )}
                  </button>
                  {!sidebarCollapsed && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirmSessionId(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-white/40 hover:text-red-400 hover:bg-red-950/30 rounded transition-all shrink-0 ml-1"
                      title="Delete conversation"
                      aria-label="Delete conversation"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* 7. Sidebar Footer (Pinned to bottom, Clean without Free Plan) */}
        <div className="p-3 border-t border-white/[0.08] bg-[#070707] shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-base text-white shrink-0 shadow-[0_0_12px_rgba(217,164,65,0.35)]"
                style={{
                  background: 'linear-gradient(135deg, #F7DE9B 0%, #D9A441 50%, #A8731F 100%)',
                }}
              >
                {userInitial}
              </div>
              {!sidebarCollapsed && (
                <div className="truncate">
                  <p className="text-[16px] font-medium text-white truncate leading-tight">
                    {userDisplayName}
                  </p>
                </div>
              )}
            </div>

            {!sidebarCollapsed && (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="p-2 rounded-lg text-[#8A8A8A] hover:text-white hover:bg-white/[0.05] transition-colors"
                  title={t('chatDashboard.settingsProfile', 'Settings & Profile')}
                >
                  <Settings className="w-5 h-5" />
                </button>

                {userDropdownOpen && (
                  <div className="absolute bottom-12 right-0 w-52 rounded-xl bg-[#121212] border border-[#D9A441]/30 p-1.5 shadow-[0_8px_30px_rgba(0,0,0,0.8)] z-50">
                    {onOpenDashboard && (
                      <button
                        onClick={() => {
                          setUserDropdownOpen(false);
                          onOpenDashboard();
                        }}
                        className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-lg flex items-center gap-2"
                      >
                        <FolderLock className="w-4 h-4 text-[#D9A441]" />
                        {t('nav.dashboard', 'Cases & Vault Dashboard')}
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setUserDropdownOpen(false);
                        if (onOpenSettings) onOpenSettings();
                      }}
                      className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-lg flex items-center gap-2"
                    >
                      <Settings className="w-4 h-4 text-[#D9A441]" />
                      {t('chatDashboard.accountSettings', 'Account Settings')}
                    </button>
                    {onOpenVault && (
                      <button
                        onClick={() => {
                          setUserDropdownOpen(false);
                          onOpenVault();
                        }}
                        className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-lg flex items-center gap-2"
                      >
                        <FolderLock className="w-4 h-4 text-[#D9A441]" />
                        {t('chatDashboard.documentVault', 'Document Vault')}
                      </button>
                    )}
                    <div className="h-[1px] bg-white/10 my-1" />
                    <button
                      onClick={handleSignOut}
                      className="w-full px-3 py-2 text-left text-xs text-red-400 hover:bg-red-500/10 rounded-lg"
                    >
                      {t('nav.signOut', 'Sign Out')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* =========================================================================
          MAIN AREA (Remaining ~80%)
          ========================================================================= */}
      <main className="relative flex-1 h-full flex flex-col overflow-hidden">
        {/* Decorative Gold Light Ribbon: Top-Center-Left */}
        <div className="absolute top-0 left-4 sm:left-12 w-[340px] sm:w-[460px] h-[220px] pointer-events-none z-[3] overflow-visible">
          <svg viewBox="0 0 500 240" fill="none" className="w-full h-full overflow-visible">
            <motion.path
              d="M-40,10 C80,20 180,90 260,110 C340,130 420,80 520,30"
              stroke="url(#goldGradientDash)"
              strokeWidth="5"
              strokeLinecap="round"
              opacity="0.18"
              filter="url(#intenseGlowDash)"
              animate={{ opacity: [0.15, 0.28, 0.15] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.path
              d="M-40,10 C80,20 180,90 260,110 C340,130 420,80 520,30"
              stroke="url(#goldGradientDash)"
              strokeWidth="1.8"
              strokeLinecap="round"
              filter="url(#goldGlowDash)"
              animate={{ opacity: [0.75, 1, 0.75] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            />
            <g transform="translate(260, 110)">
              <motion.circle
                r="3"
                fill="#FFFFFF"
                filter="url(#intenseGlowDash)"
                animate={{ scale: [1, 1.35, 1], opacity: [0.85, 1, 0.85] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
              />
              <motion.path
                d="M0,-18 L2,-2 L18,0 L2,2 L0,18 L-2,2 L-18,0 L-2,-2 Z"
                fill="url(#goldGradientDash)"
                filter="url(#goldGlowDash)"
                animate={{ scale: [0.9, 1.25, 0.9], rotate: [0, 90, 180] }}
                transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
              />
            </g>
          </svg>
        </div>

        {/* Decorative Gold Light Ribbon: Bottom-Right Corner */}
        <div className="absolute bottom-0 right-0 w-[380px] sm:w-[500px] h-[260px] pointer-events-none z-[3] overflow-visible">
          <svg viewBox="0 0 600 320" fill="none" className="w-full h-full overflow-visible">
            <motion.path
              d="M50,300 C150,260 260,200 360,190 C460,180 540,210 660,180"
              stroke="url(#goldGradientDash)"
              strokeWidth="5"
              strokeLinecap="round"
              opacity="0.18"
              filter="url(#intenseGlowDash)"
              animate={{ opacity: [0.14, 0.26, 0.14] }}
              transition={{ duration: 5.2, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.path
              d="M50,300 C150,260 260,200 360,190 C460,180 540,210 660,180"
              stroke="url(#goldGradientDash)"
              strokeWidth="1.8"
              strokeLinecap="round"
              filter="url(#goldGlowDash)"
              animate={{ opacity: [0.75, 1, 0.75] }}
              transition={{ duration: 4.2, repeat: Infinity, ease: 'easeInOut' }}
            />
          </svg>
        </div>

        {/* Top-Right Header (Language Selector + User Avatar) */}
        <div className="relative z-40 h-[76px] px-6 sm:px-8 flex items-center justify-between md:justify-end gap-4 shrink-0">
          {/* Mobile hamburger & brand */}
          <div className="flex md:hidden items-center gap-2.5">
            <button
              onClick={() => setMobileDrawerOpen(true)}
              className="p-2 rounded-lg text-white/80 hover:text-white bg-white/[0.04] cursor-pointer"
              title="Open Navigation"
            >
              <PanelLeft className="w-5 h-5" />
            </button>
            <div
              onClick={() => {
                if (onOpenDashboard) onOpenDashboard();
                else if (onNavigateHome) onNavigateHome();
              }}
              className="flex items-center gap-1.5 cursor-pointer"
              title="Return to Dashboard"
            >
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#D9A441]/20 to-[#6B4410]/20 border border-[#D9A441]/40 flex items-center justify-center shrink-0">
                <Scale className="w-3.5 h-3.5 text-[#F7DE9B]" />
              </div>
              <span className="font-serif font-bold text-base text-[#F5EEDC]">
                Law <span className="bg-gradient-to-r from-[#F7DE9B] to-[#D9A441] bg-clip-text text-transparent">Mithra</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Pill-shaped Language Selector */}
            <div className="relative">
              <button
                onClick={() => setLanguageDropdownOpen(!languageDropdownOpen)}
                className="h-[38px] px-3.5 rounded-full bg-[#070707]/80 backdrop-blur-md border border-[#D9A441]/40 hover:border-[#D9A441] shadow-[0_0_15px_rgba(217,164,65,0.12)] flex items-center gap-2 transition-all cursor-pointer group"
              >
                <Globe2 className="w-4 h-4 text-[#D9A441] group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-white">{currentLangObj.nativeName}</span>
                <ChevronDown className="w-3.5 h-3.5 text-white/70" />
              </button>

              {languageDropdownOpen && (
                <div className="absolute top-11 right-0 w-52 max-h-72 overflow-y-auto rounded-2xl bg-[#0D0D0D] border border-[#D9A441]/40 p-1.5 shadow-[0_10px_35px_rgba(0,0,0,0.85)] z-50 scrollbar-thin scrollbar-thumb-[#D9A441]/30">
                  {languages.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => {
                        setLanguage(l.code as SupportedLanguage);
                        setLanguageDropdownOpen(false);
                      }}
                      className={`w-full px-3 py-2 rounded-xl text-left text-xs flex items-center justify-between transition-colors ${
                        language === l.code
                          ? 'bg-[#D9A441]/15 text-[#F7DE9B] font-semibold border-l-2 border-[#D9A441]'
                          : 'text-white/80 hover:bg-white/[0.05] hover:text-white'
                      }`}
                    >
                      <span className="font-medium">{l.nativeName}</span>
                      <span className="text-[10px] text-white/40 uppercase">{l.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Circular gold-gradient user avatar (~48px) */}
            <div
              className="w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center font-bold text-lg text-white shrink-0 shadow-[0_0_18px_rgba(217,164,65,0.4)] border border-[#F7DE9B]/40"
              style={{
                background: 'linear-gradient(135deg, #F7DE9B 0%, #D9A441 50%, #A8731F 100%)',
              }}
            >
              {userInitial}
            </div>
          </div>
        </div>

        {/* Content Area: Empty State Hero OR Active Conversation Stream */}
        <div className="relative z-10 flex-1 overflow-y-auto px-4 sm:px-8 pb-[130px] flex flex-col justify-start">
          {messages.length === 0 ? (
            /* ===============================================================
               CENTER HERO (Vertically centered at ~42% of main area height)
               Empty state: Ornate Scales of Justice with concentric rings & sparkles
               NO TEXT UNDER LOGO (Per exact specification)
               =============================================================== */
            <div className="flex-1 flex items-center justify-center -mt-8">
              <div className="relative w-[260px] sm:w-[300px] h-[220px] sm:h-[260px] flex items-center justify-center">
                {/* Concentric Gold Rings & Glow */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div
                    className="absolute w-[200px] h-[200px] rounded-full"
                    style={{
                      background:
                        'radial-gradient(circle, rgba(217, 164, 65, 0.22) 0%, rgba(168, 115, 31, 0.08) 50%, transparent 70%)',
                    }}
                  />
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 100, repeat: Infinity, ease: 'linear' }}
                    className="absolute w-[95%] h-[95%] rounded-full border border-[#D9A441]/25 shadow-[0_0_20px_rgba(217,164,65,0.06)]"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.03, 1] }}
                    transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute w-[78%] h-[78%] rounded-full border border-[#F7DE9B]/35 border-dashed"
                  />

                  {/* Four 4-Point Gold Star Sparkles at Top, Bottom, Left, Right */}
                  <motion.div
                    animate={{ scale: [0.9, 1.3, 0.9], opacity: [0.75, 1, 0.75] }}
                    transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute top-[-8px] left-1/2 -translate-x-1/2"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                        fill="url(#goldGradientDash)"
                        filter="url(#intenseGlowDash)"
                      />
                      <circle cx="12" cy="12" r="2" fill="#FFFFFF" />
                    </svg>
                  </motion.div>

                  <motion.div
                    animate={{ scale: [0.9, 1.3, 0.9], opacity: [0.75, 1, 0.75] }}
                    transition={{ duration: 2.6, delay: 1.3, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute bottom-[-8px] left-1/2 -translate-x-1/2"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                        fill="url(#goldGradientDash)"
                        filter="url(#intenseGlowDash)"
                      />
                      <circle cx="12" cy="12" r="2" fill="#FFFFFF" />
                    </svg>
                  </motion.div>

                  <motion.div
                    animate={{ scale: [0.9, 1.3, 0.9], opacity: [0.75, 1, 0.75] }}
                    transition={{ duration: 2.6, delay: 0.65, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute left-[-8px] top-1/2 -translate-y-1/2"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                        fill="url(#goldGradientDash)"
                        filter="url(#intenseGlowDash)"
                      />
                      <circle cx="12" cy="12" r="2" fill="#FFFFFF" />
                    </svg>
                  </motion.div>

                  <motion.div
                    animate={{ scale: [0.9, 1.3, 0.9], opacity: [0.75, 1, 0.75] }}
                    transition={{ duration: 2.6, delay: 1.95, repeat: Infinity, ease: 'easeInOut' }}
                    className="absolute right-[-8px] top-1/2 -translate-y-1/2"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                        fill="url(#goldGradientDash)"
                        filter="url(#intenseGlowDash)"
                      />
                      <circle cx="12" cy="12" r="2" fill="#FFFFFF" />
                    </svg>
                  </motion.div>

                  {/* Two Thin Horizontal Gold Light Streaks Extending Left & Right */}
                  <div className="absolute left-[-32%] top-1/2 -translate-y-1/2 flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF] shadow-[0_0_10px_#F7DE9B] ring-1 ring-[#D9A441]" />
                    <span className="h-[1.5px] w-24 sm:w-32 bg-gradient-to-r from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
                  </div>
                  <div className="absolute right-[-32%] top-1/2 -translate-y-1/2 flex items-center">
                    <span className="h-[1.5px] w-24 sm:w-32 bg-gradient-to-l from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF] shadow-[0_0_10px_#F7DE9B] ring-1 ring-[#D9A441]" />
                  </div>
                </div>

                {/* Floating Scales of Justice (~150px tall) */}
                <motion.div
                  animate={{ y: [0, -7, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                  className="relative z-10 w-full h-full flex items-center justify-center"
                >
                  <img
                    src="/assets/scales-of-justice.png"
                    alt="Law Mithra Scales"
                    className="w-[150px] h-[150px] object-contain drop-shadow-[0_8px_24px_rgba(217,164,65,0.32)]"
                  />
                </motion.div>
              </div>
            </div>
          ) : (
            /* ===============================================================
               ACTIVE CONVERSATION STREAM (Takes place of scales hero)
               =============================================================== */
            <div className="max-w-4xl w-full mx-auto space-y-6 pt-4">
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'user' ? (
                    <div className="max-w-[78%] rounded-[22px] bg-gradient-to-r from-[#4A3618]/90 via-[#6B4D1F]/90 to-[#4A3618]/90 border border-[#D9A441]/50 px-5 py-3.5 text-white shadow-[0_4px_20px_rgba(217,164,65,0.18)]">
                      <p className="text-[15px] leading-relaxed font-sans">{msg.text}</p>
                      <span className="block text-[11px] text-[#F7DE9B]/70 mt-1.5 text-right">
                        {msg.timestamp}
                      </span>
                    </div>
                  ) : (
                    <div className="max-w-[85%] rounded-[22px] bg-[#0C0C0C]/90 backdrop-blur-md border border-[#D9A441]/30 p-5 text-white/95 shadow-[0_8px_32px_rgba(0,0,0,0.6)] space-y-3">
                      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
                        <div className="flex items-center gap-2">
                          <Scale className="w-4 h-4 text-[#D9A441]" />
                          <span className="text-xs font-semibold tracking-wider text-[#F7DE9B] uppercase">
                            {t('chatDashboard.aiExplanation', 'Law Mithra AI Explanation')}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopy(msg.id, msg.text)}
                            className="p-1 rounded text-white/50 hover:text-white transition-colors flex items-center gap-1 text-xs"
                            title={t('chatDashboard.copyResponse', 'Copy response')}
                          >
                            {copiedId === msg.id ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="text-[10px] text-emerald-400 font-sans">
                                  {t('chatDashboard.copied', 'Copied')}
                                </span>
                              </>
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>

                      <p className="text-[15px] leading-relaxed font-sans whitespace-pre-line text-white/90">
                        {cleanFormatting(msg.text)}
                      </p>

                      <span className="block text-[10px] text-white/40 pt-1">{msg.timestamp}</span>
                    </div>
                  )}
                </motion.div>
              ))}

              {isThinking && (
                <div className="flex justify-start">
                  <div className="rounded-[22px] bg-[#0C0C0C] border border-[#D9A441]/30 px-5 py-3.5 text-[#F7DE9B] flex items-center gap-3">
                    <Sparkles className="w-4 h-4 animate-spin text-[#D9A441]" />
                    <span className="text-sm font-sans">
                      {t('chatDashboard.analyzing', 'Analyzing legal statutes and procedures...')}
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* =========================================================================
            BOTTOM CHAT INPUT BAR
            (Centered, width ~70%, pinned ~40px from bottom, pill-shaped)
            ========================================================================= */}
        <div className="absolute bottom-6 sm:bottom-9 left-0 right-0 z-30 px-4 flex justify-center pointer-events-none">
          <div className="w-full max-w-4xl pointer-events-auto">
            <div className="relative rounded-full bg-[#0B0B0B] border border-[#D9A441]/60 px-3 sm:px-4 py-2 sm:py-2.5 flex items-center gap-2 sm:gap-3 shadow-[0_0_30px_rgba(217,164,65,0.18)] focus-within:border-[#F7DE9B] focus-within:shadow-[0_0_35px_rgba(217,164,65,0.32)] transition-all">
              {/* Left: Circular Outlined "+" Button */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setAttachMenuOpen(!attachMenuOpen)}
                  className="w-10 h-10 rounded-full border border-[#D9A441]/60 hover:border-[#D9A441] hover:bg-[#D9A441]/10 flex items-center justify-center text-white/80 hover:text-white transition-all shrink-0"
                  title={t('chatDashboard.attachTooltip', 'Attach Document')}
                >
                  <Plus className="w-5 h-5 stroke-[2]" />
                </button>

                {attachMenuOpen && (
                  <div className="absolute bottom-14 left-0 w-64 rounded-2xl bg-[#121212] border border-[#D9A441]/40 p-2 shadow-[0_10px_35px_rgba(0,0,0,0.85)] z-50">
                    {onOpenUpload && (
                      <button
                        onClick={() => {
                          setAttachMenuOpen(false);
                          onOpenUpload();
                        }}
                        className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-xl flex items-center gap-2.5"
                      >
                        <Upload className="w-4 h-4 text-[#D9A441]" />
                        {t('chatDashboard.uploadDocument', 'Upload Legal Document')}
                      </button>
                    )}
                    {onOpenVault && (
                      <button
                        onClick={() => {
                          setAttachMenuOpen(false);
                          onOpenVault();
                        }}
                        className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-xl flex items-center gap-2.5"
                      >
                        <FolderLock className="w-4 h-4 text-[#D9A441]" />
                        {t('chatDashboard.openVault', 'Open Document Vault')}
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setAttachMenuOpen(false);
                        handleSendMessage(
                          language === 'kn'
                            ? 'ನನ್ನ ಜಮೀನನ್ನು ಇನ್ನೊಬ್ಬರು ಅಕ್ರಮವಾಗಿ ಸ್ವಾಧೀನಪಡಿಸಿಕೊಂಡಿದ್ದಾರೆ. ಕಾನೂನು ಪರಿಹಾರಗಳೇನು?'
                            : language === 'hi'
                            ? 'भूमि विवाद में कानूनी उपचार क्या हैं?'
                            : 'What are the legal remedies for illegal property dispossession?'
                        );
                      }}
                      className="w-full px-3 py-2 text-left text-xs text-white/90 hover:bg-[#D9A441]/10 rounded-xl flex items-center gap-2.5"
                    >
                      <FileText className="w-4 h-4 text-[#D9A441]" />
                      {t('chatDashboard.sampleQueries', 'Sample Legal Queries')}
                    </button>
                  </div>
                )}
              </div>

              {/* Main Input Field */}
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={t('chatDashboard.inputPlaceholder', 'Ask anything about law...')}
                className="flex-1 bg-transparent text-white placeholder-[#8A8A8A] text-base sm:text-[18px] font-sans outline-none px-2"
              />

              {/* Right Side Icons: Paperclip + Mic + Circular Send Button */}
              <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                {/* Paperclip (Attach file) */}
                <button
                  type="button"
                  onClick={() => onOpenUpload && onOpenUpload()}
                  className="p-2 text-white/60 hover:text-white transition-colors"
                  title={t('chatDashboard.attachTooltip', 'Attach Document')}
                >
                  <Paperclip className="w-5 h-5" />
                </button>

                {/* Microphone (Voice input) */}
                <button
                  type="button"
                  onClick={handleVoiceToggle}
                  className={`p-2 transition-colors ${
                    isListening ? 'text-red-400 animate-pulse' : 'text-white/60 hover:text-white'
                  }`}
                  title={
                    isListening
                      ? t('chatDashboard.voiceListening', 'Listening...')
                      : t('chatDashboard.voiceTooltip', 'Voice Input')
                  }
                >
                  <Mic className="w-5 h-5" />
                </button>

                {/* Circular Gold-Gradient Send Button (~52px) */}
                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || isThinking}
                  className="w-11 h-11 sm:w-[50px] sm:h-[50px] rounded-full flex items-center justify-center text-[#111] shadow-[0_0_20px_rgba(217,164,65,0.4)] hover:shadow-[0_0_28px_rgba(217,164,65,0.65)] hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, #F7DE9B 0%, #D9A441 50%, #A8731F 100%)',
                  }}
                  title={t('chatDashboard.sendTooltip', 'Send Message')}
                >
                  <Send className="w-5 h-5 fill-[#111] text-[#111] translate-x-0.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileDrawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileDrawerOpen(false)}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 md:hidden"
            />
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 left-0 bottom-0 w-[300px] bg-[#070707] border-r border-[#D9A441]/20 z-50 flex flex-col md:hidden"
            >
              <div className="h-[70px] px-5 flex items-center justify-between border-b border-white/[0.06]">
                <div className="flex items-center gap-3">
                  <Scale className="w-5 h-5 text-[#F7DE9B]" />
                  <span className="font-serif font-bold text-xl text-white">
                    {t('brand.title', 'Law Mithra')}
                  </span>
                </div>
                <button
                  onClick={() => setMobileDrawerOpen(false)}
                  className="p-1.5 text-white/60 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4">
                <button
                  onClick={() => {
                    handleNewChat();
                    setMobileDrawerOpen(false);
                  }}
                  className="w-full h-[48px] rounded-xl bg-gradient-to-r from-[#5C4420] via-[#8A6A2E] to-[#4A3618] border border-[#D9A441] text-white font-medium flex items-center justify-center gap-3"
                >
                  <Plus className="w-4 h-4" />
                  {t('chatDashboard.newChat', 'New Chat')}
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-white/50 uppercase tracking-wider font-semibold">
                    {t('chatDashboard.recentChats', 'Recent Chats')}
                  </p>
                  {sessionsLoading && <Loader2 className="w-3.5 h-3.5 text-[#D9A441] animate-spin" />}
                </div>
                {filteredChats.length === 0 ? (
                  <p className="py-4 text-xs text-white/40 italic">
                    {t('chatDashboard.noRecentChats', 'No recent chats')}
                  </p>
                ) : (
                  filteredChats.map((session) => (
                    <div
                      key={session.id}
                      className="w-full py-2.5 px-3 rounded-lg text-left text-sm text-white/80 hover:bg-white/[0.05] flex items-center justify-between gap-3"
                    >
                      <button
                        onClick={() => {
                          handleSelectSession(session);
                          setMobileDrawerOpen(false);
                        }}
                        className="flex items-center gap-3 min-w-0 flex-1 text-left"
                      >
                        <MessageSquare className="w-4 h-4 text-[#D9A441] shrink-0" />
                        <span className="truncate">{session.title}</span>
                      </button>
                      <button
                        onClick={() => setDeleteConfirmSessionId(session.id)}
                        className="p-1 text-white/40 hover:text-red-400"
                        title="Delete conversation"
                        aria-label="Delete conversation"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>

              <div className="p-4 border-t border-white/[0.06] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white"
                    style={{
                      background: 'linear-gradient(135deg, #F7DE9B 0%, #D9A441 50%, #A8731F 100%)',
                    }}
                  >
                    {userInitial}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{userDisplayName}</p>
                  </div>
                </div>

                <button
                  onClick={handleSignOut}
                  className="text-xs text-red-400 hover:text-red-300 font-medium px-2 py-1 rounded hover:bg-red-500/10"
                >
                  {t('nav.signOut', 'Sign Out')}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      {deleteConfirmSessionId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-[#141414] border border-[#D9A441]/40 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-amber-400 mb-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h3 className="font-semibold text-base text-white">Delete Conversation?</h3>
            </div>
            <p className="text-sm text-white/70 mb-5">
              This conversation thread and all its legal advice turns will be permanently removed. This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirmSessionId(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-sm font-medium text-white/80 hover:bg-white/10 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteSession(deleteConfirmSessionId)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-sm font-semibold bg-red-600 hover:bg-red-500 text-white transition-colors flex items-center gap-2 cursor-pointer"
              >
                {isDeleting && <Loader2 className="w-4 h-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatDashboardPage;
