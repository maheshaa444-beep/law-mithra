import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Sparkles,
  Scale,
  ShieldAlert,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Globe,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  User as UserIcon,
} from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { SupportedLanguage } from '@/lib/translations';
import { askLegalAssistant } from '@/lib/api';

interface ApplicableSection {
  act: string;
  sections: string[];
  summary: string;
  original_english_statute: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  detectedLanguage?: string;
  targetLanguage?: string;
  legalIssue?: string;
  remedies?: string[];
  applicableSections?: ApplicableSection[];
  disclaimer?: string;
  timestamp: Date;
}

interface LegalAssistantChatProps {
  onClose?: () => void;
  standalone?: boolean;
}

export function LegalAssistantChat({ onClose, standalone = false }: LegalAssistantChatProps) {
  const { language, setLanguage, currentLanguage, languages, t } = useLanguage();

  const [inputQuery, setInputQuery] = useState('');
  const [autoDetectLang, setAutoDetectLang] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: 'welcome',
      role: 'assistant',
      content: t('chat.subtitle', 'Instant procedural guidance under Indian law in 10 languages.'),
      disclaimer: t('chat.disclaimer', 'This legal explanation is generated for informational guidance and does not replace formal legal counsel from an enrolled advocate.'),
      timestamp: new Date(),
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedStatuteId, setExpandedStatuteId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const samplePrompts = [
    t('chat.samplePrompt1', 'Someone has illegally encroached on my agricultural land. What legal remedies do I have?'),
    t('chat.samplePrompt2', 'A cheque issued to me has bounced due to insufficient funds. What is the procedure?'),
  ];

  const handleSend = async (queryToSend?: string) => {
    const text = (queryToSend || inputQuery).trim();
    if (!text || isSubmitting) return;

    setErrorMessage(null);
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsSubmitting(true);

    try {
      const data = await askLegalAssistant(text, language, autoDetectLang);

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: data.explanation || data.legal_issue || t('chat.subtitle'),
        detectedLanguage: data.detected_language,
        targetLanguage: data.target_language,
        legalIssue: data.legal_issue,
        remedies: data.remedies || [],
        applicableSections: data.applicable_sections || [],
        disclaimer: data.disclaimer,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to communicate with Legal AI.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className={`flex flex-col bg-charcoal text-slate-100 rounded-[24px] border border-gold-500/30 shadow-2xl overflow-hidden ${standalone ? 'h-[750px] max-h-[88vh] w-full max-w-4xl mx-auto' : 'h-full'}`}>
      
      {/* Top Header */}
      <div className="px-6 py-4 border-b border-gold-500/20 bg-charcoal-300/80 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-gold-400/20 to-gold-600/10 border border-gold-400/40 flex items-center justify-center text-gold-400 shadow-soft">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-serif font-bold text-lg text-ivory flex items-center gap-2">
              <span>{t('chat.title', 'Law Mithra Multilingual Legal AI')}</span>
              <span className="text-[10px] uppercase font-sans tracking-widest px-2 py-0.5 rounded-full bg-gold-500/20 text-gold-300 border border-gold-500/30">
                10 Languages
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              {t('chat.subtitle', 'Instant procedural guidance under Indian law in 10 languages')}
            </p>
          </div>
        </div>

        {/* Options & Controls */}
        <div className="flex items-center gap-3">
          {/* Language Toggle Options */}
          <div className="hidden sm:flex items-center gap-2 bg-charcoal-400/90 border border-gold-500/20 rounded-full px-3 py-1 text-xs">
            <Globe className="w-3.5 h-3.5 text-gold-400" />
            <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 select-none">
              <input
                type="checkbox"
                checked={autoDetectLang}
                onChange={(e) => setAutoDetectLang(e.target.checked)}
                className="rounded border-gold-500/50 text-gold-500 focus:ring-gold-500/40 bg-charcoal-200"
              />
              <span>{t('chat.autoDetect', 'Auto-detect input language')}</span>
            </label>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-charcoal-200 transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-navy-900 border border-gold-500/30 text-gold-400 flex items-center justify-center shrink-0 mt-1 shadow-soft">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div className={`max-w-[85%] rounded-[20px] p-4 sm:p-5 ${msg.role === 'user' ? 'bg-gold-500 text-charcoal-900 font-medium ml-12 shadow-gold' : 'bg-charcoal-200/90 border border-gold-500/20 text-slate-100 shadow-soft'}`}>
              
              {/* User text */}
              {msg.role === 'user' && (
                <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              )}

              {/* Assistant Response Card */}
              {msg.role === 'assistant' && (
                <div className="space-y-4">
                  {/* Language & Issue Header */}
                  {msg.legalIssue && (
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-charcoal-100">
                      <span className="text-xs font-semibold text-gold-400 tracking-wide uppercase">
                        {t('chat.identifiedIssue', 'Identified Legal Issue')}
                      </span>
                      {msg.targetLanguage && (
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-charcoal-300 border border-gold-500/20 text-slate-300 font-sans">
                          {SUPPORTED_LANGUAGES_MAP[msg.targetLanguage] || msg.targetLanguage}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Legal Issue Statement */}
                  {msg.legalIssue && (
                    <h4 className="font-serif font-bold text-base sm:text-lg text-ivory">
                      {msg.legalIssue}
                    </h4>
                  )}

                  {/* Summary content */}
                  {!msg.remedies && (
                    <p className="text-sm text-slate-200 leading-relaxed">{msg.content}</p>
                  )}

                  {/* Step-by-Step Remedies in Regional Language */}
                  {msg.remedies && msg.remedies.length > 0 && (
                    <div className="space-y-2.5 mt-2">
                      <p className="text-xs font-bold uppercase tracking-wider text-gold-400">
                        {t('chat.statutoryRemedies', 'Recommended Statutory Remedies & Next Steps')}
                      </p>
                      <div className="space-y-2">
                        {msg.remedies.map((remedy, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-charcoal-300/80 border border-gold-500/15 text-xs sm:text-sm text-slate-100 leading-relaxed font-sans"
                          >
                            {remedy}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Applicable Statutes & Dual English View */}
                  {msg.applicableSections && msg.applicableSections.length > 0 && (
                    <div className="space-y-2.5 pt-2">
                      <p className="text-xs font-bold uppercase tracking-wider text-gold-400">
                        {t('chat.applicableStatutes', 'Applicable Sections & Legal Citations')}
                      </p>
                      <div className="grid grid-cols-1 gap-2.5">
                        {msg.applicableSections.map((sec, idx) => {
                          const isExpanded = expandedStatuteId === `${msg.id}-${idx}`;
                          return (
                            <div
                              key={idx}
                              className="rounded-xl border border-charcoal-100 bg-charcoal-300/40 p-3.5 space-y-2 transition-colors"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2">
                                  <BookOpen className="w-4 h-4 text-gold-400 shrink-0" />
                                  <span className="font-bold text-xs sm:text-sm text-ivory">
                                    {sec.act} — {sec.sections.join(', ')}
                                  </span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setExpandedStatuteId(isExpanded ? null : `${msg.id}-${idx}`)
                                  }
                                  className="text-[11px] text-gold-400 hover:text-gold-300 font-medium flex items-center gap-1 cursor-pointer"
                                >
                                  <span>
                                    {isExpanded
                                      ? t('chat.hideOriginalEnglish', 'Hide English Reference')
                                      : t('chat.viewOriginalEnglish', 'View Statutory English Reference')}
                                  </span>
                                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>
                              </div>

                              <p className="text-xs text-slate-300 font-sans">{sec.summary}</p>

                              {/* Collapsible Verified English Statute (Rule 6 Safeguard) */}
                              <AnimatePresence>
                                {isExpanded && (
                                  <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="pt-2 border-t border-charcoal-100"
                                  >
                                    <div className="p-2.5 rounded-lg bg-navy-950/60 border border-gold-500/20 text-xs text-slate-200 font-mono leading-relaxed">
                                      <p className="text-[10px] text-gold-400/90 font-bold uppercase mb-1">
                                        Verified Statutory Law Provision (English):
                                      </p>
                                      {sec.original_english_statute}
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Prominent Non-Official Disclaimer */}
                  {msg.disclaimer && (
                    <div className="p-2.5 rounded-xl bg-charcoal-400/50 border border-gold-500/10 text-[11px] text-slate-400 leading-snug flex items-start gap-2">
                      <ShieldAlert className="w-4 h-4 text-gold-400/80 shrink-0 mt-0.5" />
                      <span>{msg.disclaimer}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-xl bg-gold-500/20 border border-gold-500/40 text-gold-400 flex items-center justify-center shrink-0 mt-1">
                <UserIcon className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isSubmitting && (
          <div className="flex gap-3 items-center text-slate-400 text-xs py-2">
            <Loader2 className="w-4 h-4 animate-spin text-gold-400" />
            <span>{t('chat.thinking', 'Analyzing facts under Indian statutes...')}</span>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* Suggested Prompt Chips */}
      {messages.length <= 1 && (
        <div className="px-6 py-2 border-t border-charcoal-200 bg-charcoal-300/40 flex flex-wrap gap-2">
          {samplePrompts.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(prompt)}
              className="text-left text-xs px-3 py-1.5 rounded-full bg-charcoal-200 border border-gold-500/20 text-slate-300 hover:text-white hover:border-gold-500/40 transition-colors"
            >
              💡 {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <div className="p-4 sm:p-5 border-t border-gold-500/20 bg-charcoal-300/90">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2 sm:gap-3"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={t('chat.placeholder', 'Ask any legal question in your regional language...')}
            className="flex-1 bg-charcoal-200 text-white placeholder-slate-400 text-xs sm:text-sm px-4 py-3 rounded-xl border border-charcoal-100 focus:outline-none focus:border-gold-500/60 focus:ring-1 focus:ring-gold-500/40 transition-all"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || isSubmitting}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-gold-500 via-gold-400 to-gold-600 text-charcoal font-bold text-xs sm:text-sm flex items-center gap-2 hover:shadow-gold active:scale-[0.98] transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>{t('chat.send', 'Ask Legal AI')}</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

const SUPPORTED_LANGUAGES_MAP: Record<string, string> = {
  en: 'English',
  hi: 'हिन्दी (Hindi)',
  kn: 'ಕನ್ನಡ (Kannada)',
  ta: 'தமிழ் (Tamil)',
  te: 'తెలుగు (Telugu)',
  ml: 'മലയാളം (Malayalam)',
  mr: 'मराठी (Marathi)',
  bn: 'বাংলা (Bengali)',
  gu: 'ગુજરાતી (Gujarati)',
  pa: 'ਪੰਜਾਬੀ (Punjabi)',
};

export default LegalAssistantChat;

