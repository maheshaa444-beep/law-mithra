import React, { useState, useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { User, Mail, Lock, ShieldCheck, Eye, EyeOff, Globe2, Loader2, ArrowRight, AlertCircle, ArrowLeft } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/Toast';
import { useLanguage } from '@/context/LanguageContext';
import { GoldLanguageSwitch } from '@/components/GoldLanguageSwitch';
import { SupportedLanguage } from '@/lib/translations';

interface SignupPageProps {
  onNavigateLogin: () => void;
  onSignupSuccess: () => void;
  onNavigateHome?: () => void;
}

export function SignupPage({ onNavigateLogin, onSignupSuccess, onNavigateHome }: SignupPageProps) {
  const { register } = useAuth();
  const { addToast } = useToast();
  const { language, setLanguage, t, languages } = useLanguage();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState<string>(language);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync preferredLanguage with active global language
  useEffect(() => {
    setPreferredLanguage(language);
  }, [language]);

  // Mouse parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 120 };
  const smoothMouseX = useSpring(mouseX, springConfig);
  const smoothMouseY = useSpring(mouseY, springConfig);

  const courthouseX = useTransform(smoothMouseX, [-1, 1], [-10, 10]);
  const courthouseY = useTransform(smoothMouseY, [-1, 1], [-6, 6]);
  const booksX = useTransform(smoothMouseX, [-1, 1], [10, -10]);
  const booksY = useTransform(smoothMouseY, [-1, 1], [8, -8]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { clientWidth, clientHeight } = e.currentTarget;
    const x = (e.clientX / clientWidth) * 2 - 1;
    const y = (e.clientY / clientHeight) * 2 - 1;
    mouseX.set(x);
    mouseY.set(y);
  };

  const validate = (): string | null => {
    const cleanName = fullName.trim();
    if (!cleanName || cleanName.length < 2) {
      return 'Please enter your full name (minimum 2 characters).';
    }
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      return 'Please enter your email address.';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanEmail)) {
      return 'Please enter a valid email address.';
    }
    if (password.length < 8) {
      return 'Password must be at least 8 characters long.';
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match. Please re-enter your confirm password.';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const validationError = validate();
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
        preferred_language: preferredLanguage,
        text_size: 'normal',
      });

      addToast({
        title: 'Account Created',
        description: 'Your private Law Mithra vault is ready.',
        variant: 'success',
      });
      onSignupSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check the information provided.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      className="relative w-screen h-screen overflow-x-hidden overflow-y-auto md:overflow-hidden bg-[#050505] text-white flex items-center justify-center select-none"
      style={{
        background: 'radial-gradient(circle at 50% 50%, #0F0D09 0%, #080808 45%, #050505 100%)',
      }}
    >
      {/* Background Texture & Noise */}
      <svg className="pointer-events-none fixed inset-0 w-full h-full opacity-[0.035] z-[1]">
        <filter id="noiseFilterSignup">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noiseFilterSignup)" />
      </svg>

      {/* Vignette */}
      <div
        className="pointer-events-none absolute inset-0 z-[2]"
        style={{
          background: 'radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(3, 3, 3, 0.6) 75%, rgba(0, 0, 0, 0.95) 100%)',
        }}
      />

      {/* Gradients & Filters */}
      <svg className="absolute w-0 h-0" aria-hidden="true" focusable="false">
        <defs>
          <linearGradient id="goldGradientSignup" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F7DE9B" />
            <stop offset="45%" stopColor="#D9A441" />
            <stop offset="80%" stopColor="#A8731F" />
            <stop offset="100%" stopColor="#6B4410" />
          </linearGradient>

          <linearGradient id="goldHorizontalSignup" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#F7DE9B" />
            <stop offset="50%" stopColor="#D9A441" />
            <stop offset="100%" stopColor="#A8731F" />
          </linearGradient>

          <filter id="goldGlowSignup" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="intenseGlowSignup" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur2" />
            <feMerge>
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>

      {/* Top-Left Gold Light Ribbon */}
      <div className="absolute top-0 left-0 w-[300px] sm:w-[420px] lg:w-[500px] h-[220px] sm:h-[300px] pointer-events-none z-[4] overflow-visible">
        <svg viewBox="0 0 600 360" fill="none" className="w-full h-full overflow-visible">
          <motion.path
            d="M-50,20 C140,25 240,110 320,130 C410,150 490,90 560,30"
            stroke="url(#goldGradientSignup)"
            strokeWidth="6"
            strokeLinecap="round"
            opacity="0.22"
            filter="url(#intenseGlowSignup)"
            animate={{ opacity: [0.18, 0.3, 0.18] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.path
            d="M-50,20 C140,25 240,110 320,130 C410,150 490,90 560,30"
            stroke="url(#goldGradientSignup)"
            strokeWidth="2.2"
            strokeLinecap="round"
            filter="url(#goldGlowSignup)"
            animate={{ opacity: [0.75, 1, 0.75] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          <g transform="translate(320, 130)">
            <motion.circle
              r="3.5"
              fill="#FFFFFF"
              filter="url(#intenseGlowSignup)"
              animate={{ scale: [1, 1.35, 1], opacity: [0.85, 1, 0.85] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.path
              d="M0,-22 L2,-3 L22,0 L2,3 L0,22 L-2,3 L-22,0 L-2,-3 Z"
              fill="url(#goldGradientSignup)"
              filter="url(#goldGlowSignup)"
              animate={{ scale: [0.9, 1.25, 0.9], rotate: [0, 90, 180] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
            />
          </g>
        </svg>
      </div>

      {/* Bottom-Right Gold Ribbon */}
      <div className="absolute bottom-0 right-0 w-[300px] sm:w-[420px] lg:w-[500px] h-[220px] sm:h-[300px] pointer-events-none z-[4] overflow-visible">
        <svg viewBox="0 0 600 340" fill="none" className="w-full h-full overflow-visible">
          <motion.path
            d="M40,330 C120,280 220,220 310,210 C410,200 500,240 650,220"
            stroke="url(#goldGradientSignup)"
            strokeWidth="5"
            strokeLinecap="round"
            opacity="0.2"
            filter="url(#intenseGlowSignup)"
            animate={{ opacity: [0.15, 0.28, 0.15] }}
            transition={{ duration: 4.8, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.path
            d="M40,330 C120,280 220,220 310,210 C410,200 500,240 650,220"
            stroke="url(#goldGradientSignup)"
            strokeWidth="1.8"
            strokeLinecap="round"
            filter="url(#goldGlowSignup)"
            animate={{ opacity: [0.75, 1, 0.75] }}
            transition={{ duration: 3.8, repeat: Infinity, ease: 'easeInOut' }}
          />
        </svg>
      </div>

      {/* Bottom-Left Courthouse */}
      <motion.div
        style={{ x: courthouseX, y: courthouseY }}
        className="absolute -bottom-6 -left-6 sm:bottom-0 sm:left-0 w-[240px] sm:w-[340px] md:w-[420px] lg:w-[480px] pointer-events-none z-[3] opacity-20 sm:opacity-25"
      >
        <div
          className="relative w-full overflow-hidden"
          style={{
            maskImage: 'radial-gradient(circle at 35% 85%, black 40%, transparent 85%)',
            WebkitMaskImage: 'radial-gradient(circle at 35% 85%, black 40%, transparent 85%)',
          }}
        >
          <img
            src="/assets/courthouse.png"
            alt=""
            className="w-full h-auto object-contain filter grayscale contrast-[115%] brightness-[85%] sepia-[25%]"
          />
        </div>
      </motion.div>

      {/* Bottom-Right Law Books */}
      <motion.div
        style={{ x: booksX, y: booksY }}
        className="absolute -bottom-8 -right-8 sm:bottom-0 sm:right-2 w-[220px] sm:w-[300px] md:w-[360px] pointer-events-none z-[3] opacity-30 sm:opacity-35"
      >
        <div
          className="relative w-full overflow-hidden"
          style={{
            maskImage: 'radial-gradient(circle at 75% 80%, black 45%, transparent 88%)',
            WebkitMaskImage: 'radial-gradient(circle at 75% 80%, black 45%, transparent 88%)',
          }}
        >
          <img
            src="/assets/law-books.png"
            alt=""
            className="w-full h-auto object-contain filter contrast-[110%] brightness-[75%]"
          />
        </div>
      </motion.div>

      {/* Top Header: Back to Home & Language Switcher */}
      {onNavigateHome && (
        <div className="absolute top-5 sm:top-7 left-5 sm:right-auto sm:left-8 lg:left-12 z-50">
          <button
            type="button"
            onClick={onNavigateHome}
            className="group inline-flex items-center gap-2 px-3.5 py-2 rounded-full border border-[#D9A441]/50 hover:border-[#F7DE9B] bg-[#0A0A0A]/85 hover:bg-[#14120D] text-white/90 hover:text-white text-xs font-sans transition-all cursor-pointer backdrop-blur-md"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-[#D9A441] group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to Home</span>
          </button>
        </div>
      )}

      {/* Top-Right Language Switcher */}
      <div className="absolute top-5 sm:top-7 right-5 sm:right-8 lg:right-12 z-50">
        <GoldLanguageSwitch />
      </div>

      {/* =========================================================================
          BALANCED SIDE-BY-SIDE CONTAINER: LOGO PANEL & SIGNUP CARD
          ========================================================================= */}
      <div className="relative z-10 w-full max-w-5xl mx-auto px-4 sm:px-8 py-4 sm:py-6 flex flex-col md:flex-row items-center justify-center gap-8 lg:gap-14 xl:gap-16">

        {/* ---------------------------------------------------------------------
            LEFT: BRAND PANEL (Scales, Title, Subtitles)
            --------------------------------------------------------------------- */}
        <div className="flex flex-col items-center text-center w-full max-w-[340px] lg:max-w-[380px] shrink-0">
          {/* Top 4-point gold sparkle */}
          <motion.div
            animate={{ scale: [0.9, 1.25, 0.9], opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
            className="mb-1"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                fill="url(#goldGradientSignup)"
                filter="url(#intenseGlowSignup)"
              />
              <circle cx="12" cy="12" r="2.5" fill="#FFFFFF" />
            </svg>
          </motion.div>

          {/* Scales of Justice with concentric rings and streaks */}
          <div className="relative w-[210px] sm:w-[240px] lg:w-[270px] h-[170px] sm:h-[190px] lg:h-[220px] flex items-center justify-center">
            {/* Concentric rings */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div
                className="absolute w-[180px] h-[180px] rounded-full"
                style={{
                  background: 'radial-gradient(circle, rgba(217, 164, 65, 0.22) 0%, rgba(168, 115, 31, 0.08) 50%, transparent 70%)',
                }}
              />
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 100, repeat: Infinity, ease: 'linear' }}
                className="absolute w-[92%] h-[92%] rounded-full border border-[#D9A441]/20 shadow-[0_0_20px_rgba(217,164,65,0.06)]"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 80, repeat: Infinity, ease: 'linear' }}
                className="absolute w-[76%] h-[76%] rounded-full border border-[#D9A441]/30 border-dashed"
              />
              <motion.div
                animate={{ scale: [1, 1.03, 1] }}
                transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute w-[58%] h-[58%] rounded-full border border-[#F7DE9B]/35"
              />

              {/* Horizontal streaks */}
              <div className="absolute left-[-22%] top-1/2 -translate-y-1/2 flex items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF] shadow-[0_0_10px_#F7DE9B] ring-1 ring-[#D9A441]" />
                <span className="h-[1.5px] w-16 sm:w-24 bg-gradient-to-r from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
              </div>
              <div className="absolute right-[-22%] top-1/2 -translate-y-1/2 flex items-center">
                <span className="h-[1.5px] w-16 sm:w-24 bg-gradient-to-l from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
                <span className="w-1.5 h-1.5 rounded-full bg-[#FFFFFF] shadow-[0_0_10px_#F7DE9B] ring-1 ring-[#D9A441]" />
              </div>
            </div>

            {/* Floating Scales */}
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="relative z-10 w-full h-full flex items-center justify-center cursor-pointer"
              onClick={onNavigateHome}
              title="Return to Home"
            >
              <img
                src="/assets/scales-of-justice.png"
                alt="Law Mithra Scales of Justice"
                className="w-[82%] h-[82%] object-contain drop-shadow-[0_10px_22px_rgba(217,164,65,0.28)]"
              />
            </motion.div>
          </div>

          {/* Title: "Law Mithra" */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mt-1 cursor-pointer"
            onClick={onNavigateHome}
          >
            <h1 className="font-serif font-bold text-3xl sm:text-4xl lg:text-[40px] tracking-tight leading-tight flex items-baseline justify-center">
              <span className="bg-gradient-to-b from-[#FFFFFF] via-[#FAF7F0] to-[#DDD2BE] bg-clip-text text-transparent drop-shadow-[0_2px_12px_rgba(255,255,255,0.18)]">
                Law
              </span>
              <span className="ml-2.5 bg-gradient-to-r from-[#F7DE9B] via-[#D9A441] to-[#A8731F] bg-clip-text text-transparent drop-shadow-[0_4px_20px_rgba(217,164,65,0.38)]">
                Mithra
              </span>
            </h1>
          </motion.div>

          {/* Divider Line with Diamond */}
          <motion.div
            initial={{ opacity: 0, scaleX: 0.6 }}
            animate={{ opacity: 1, scaleX: 1 }}
            transition={{ duration: 0.6, delay: 0.25 }}
            className="flex items-center justify-center my-2.5 w-40 sm:w-48"
          >
            <span className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#D9A441]/80 to-[#D9A441]" />
            <span className="mx-2 flex items-center justify-center">
              <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6,0 L7.5,4.5 L12,6 L7.5,7.5 L6,12 L4.5,7.5 L0,6 L4.5,4.5 Z"
                  fill="url(#goldGradientSignup)"
                  filter="url(#goldGlowSignup)"
                />
                <circle cx="6" cy="6" r="1.3" fill="#FFFFFF" />
              </svg>
            </span>
            <span className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[#D9A441]/80 to-[#D9A441]" />
          </motion.div>

          {/* Subtitles */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className="space-y-0.5 font-sans text-xs sm:text-[13px] text-white tracking-wide"
          >
            <p className="font-normal opacity-90">{t('brand.tagline', 'Your Smart Legal Assistant')}</p>
            <p className="font-normal opacity-90">
              {t('brand.languageScope', 'in Every Indian Language')}
            </p>
          </motion.div>
        </div>

        {/* ---------------------------------------------------------------------
            RIGHT: SIGNUP CARD (Directly beside logo, vertically balanced)
            --------------------------------------------------------------------- */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-[440px] sm:max-w-[480px] lg:max-w-[500px] shrink-0"
        >
          {/* Card Glass Container */}
          <div className="relative rounded-[26px] bg-[rgba(10,10,10,0.85)] backdrop-blur-md border border-[#C8963E] p-6 sm:p-7 lg:p-8 shadow-[0_0_35px_rgba(200,150,62,0.18)]">

            {/* Bright gold light highlight at center of TOP edge */}
            <motion.div
              animate={{ opacity: [0.75, 1, 0.75], scaleX: [0.92, 1.08, 0.92] }}
              transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-28 sm:w-36 h-[2.5px] rounded-full bg-gradient-to-r from-transparent via-[#F7DE9B] to-transparent shadow-[0_0_12px_#D9A441]"
            />

            {/* Bright gold light highlight at center of BOTTOM edge */}
            <motion.div
              animate={{ opacity: [0.75, 1, 0.75], scaleX: [0.92, 1.08, 0.92] }}
              transition={{ duration: 3.2, delay: 1.6, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-28 sm:w-36 h-[2.5px] rounded-full bg-gradient-to-r from-transparent via-[#F7DE9B] to-transparent shadow-[0_0_12px_#D9A441]"
            />

            {/* Heading: "Create Account" */}
            <div className="text-center">
              <h2 className="font-serif font-bold text-2xl sm:text-3xl leading-tight">
                <span className="text-white">{t('signup.create', 'Create')} </span>
                <span className="bg-gradient-to-r from-[#F7DE9B] via-[#D9A441] to-[#A8731F] bg-clip-text text-transparent">
                  {t('signup.account', 'Account')}
                </span>
              </h2>
              <p className="font-sans text-white/90 text-xs sm:text-[13px] mt-1">
                {t('signup.subtitle', 'Secure, confidential legal assistance tailored for Indian citizens')}
              </p>
            </div>

            {/* Inline Error Message */}
            {errorMessage && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-3.5 p-2.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span className="flex-1 font-sans leading-snug">{errorMessage}</span>
              </motion.div>
            )}

            {/* Signup Form */}
            <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
              {/* Input 1: Full Name */}
              <div>
                <div className="h-[48px] sm:h-[52px] w-full rounded-[15px] bg-[#0D0D0D] border border-[#6B4D1F] px-4 sm:px-5 flex items-center gap-3 transition-all duration-200 focus-within:border-[#D9A441] focus-within:shadow-[0_0_18px_rgba(217,164,65,0.22)]">
                  <User className="w-4 h-4 sm:w-5 sm:h-5 text-[#D9A441] shrink-0" />
                  <input
                    type="text"
                    autoFocus
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t('signup.fullNamePlaceholder', 'Full Name (e.g. Shiva Prasad)')}
                    className="w-full bg-transparent text-white placeholder-[#7A7A7A] text-xs sm:text-sm font-sans outline-none"
                  />
                </div>
              </div>

              {/* Input 2: Email Address */}
              <div>
                <div className="h-[48px] sm:h-[52px] w-full rounded-[15px] bg-[#0D0D0D] border border-[#6B4D1F] px-4 sm:px-5 flex items-center gap-3 transition-all duration-200 focus-within:border-[#D9A441] focus-within:shadow-[0_0_18px_rgba(217,164,65,0.22)]">
                  <Mail className="w-4 h-4 sm:w-5 sm:h-5 text-[#D9A441] shrink-0" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t('signup.emailPlaceholder', 'your.email@example.com')}
                    className="w-full bg-transparent text-white placeholder-[#7A7A7A] text-xs sm:text-sm font-sans outline-none"
                  />
                </div>
                <p className="text-[10px] text-[#8C8476] mt-1 px-1">{t('signup.emailHelper', 'Your email will serve as your username.')}</p>
              </div>

              {/* Input 3: Password */}
              <div className="h-[48px] sm:h-[52px] w-full rounded-[15px] bg-[#0D0D0D] border border-[#6B4D1F] px-4 sm:px-5 flex items-center gap-3 transition-all duration-200 focus-within:border-[#D9A441] focus-within:shadow-[0_0_18px_rgba(217,164,65,0.22)]">
                <Lock className="w-4 h-4 sm:w-5 sm:h-5 text-[#D9A441] shrink-0" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('signup.passwordPlaceholder', 'Password (min. 8 characters)')}
                  className="w-full bg-transparent text-white placeholder-[#7A7A7A] text-xs sm:text-sm font-sans outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-[#7A7A7A] hover:text-[#D9A441] transition-colors p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
              </div>

              {/* Input 4: Confirm Password */}
              <div className="h-[48px] sm:h-[52px] w-full rounded-[15px] bg-[#0D0D0D] border border-[#6B4D1F] px-4 sm:px-5 flex items-center gap-3 transition-all duration-200 focus-within:border-[#D9A441] focus-within:shadow-[0_0_18px_rgba(217,164,65,0.22)]">
                <ShieldCheck className="w-4 h-4 sm:w-5 sm:h-5 text-[#D9A441] shrink-0" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t('signup.confirmPasswordPlaceholder', 'Confirm Password')}
                  className="w-full bg-transparent text-white placeholder-[#7A7A7A] text-xs sm:text-sm font-sans outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-[#7A7A7A] hover:text-[#D9A441] transition-colors p-1"
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                >
                  {showConfirmPassword ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
              </div>

              {/* Preferred Language Select */}
              <div className="h-[48px] sm:h-[52px] w-full rounded-[15px] bg-[#0D0D0D] border border-[#6B4D1F] px-4 sm:px-5 flex items-center gap-3 transition-all duration-200 focus-within:border-[#D9A441] focus-within:shadow-[0_0_18px_rgba(217,164,65,0.22)]">
                <Globe2 className="w-4 h-4 sm:w-5 sm:h-5 text-[#D9A441] shrink-0" />
                <select
                  value={preferredLanguage}
                  onChange={(e) => {
                    const nextLang = e.target.value;
                    setPreferredLanguage(nextLang);
                    setLanguage(nextLang as SupportedLanguage);
                  }}
                  className="w-full bg-transparent text-white text-xs sm:text-sm font-sans outline-none cursor-pointer"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code} className="bg-[#141414] text-white">
                      {lang.nativeName} ({lang.name})
                    </option>
                  ))}
                </select>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full h-[48px] sm:h-[52px] rounded-[15px] bg-gradient-to-r from-[#C9953A] via-[#F2D488] to-[#C9953A] hover:shadow-[0_0_26px_rgba(242,212,136,0.45)] hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99] transition-all duration-200 font-sans font-bold text-sm sm:text-base tracking-wide text-[#111] flex items-center justify-center gap-2 disabled:opacity-75 disabled:pointer-events-none cursor-pointer mt-1"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin text-[#111]" />
                    <span>{t('signup.creating', 'Creating account...')}</span>
                  </>
                ) : (
                  <>
                    <span>{t('signup.button', 'Create Private Account')}</span>
                    <ArrowRight className="w-5 h-5 stroke-[2.5]" />
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center justify-center my-3.5">
              <span className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#6B4D1F]/60 to-[#6B4D1F]/80" />
              <span className="px-3 text-[11px] font-medium text-[#7A7A7A] tracking-wider uppercase">
                {t('common.or', 'OR')}
              </span>
              <span className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[#6B4D1F]/60 to-[#6B4D1F]/80" />
            </div>

            {/* Footer */}
            <div className="text-center font-sans text-xs text-white/70">
              <span>{t('login.alreadyHaveAccount', 'Already have an account?')} </span>
              <button
                type="button"
                onClick={onNavigateLogin}
                className="text-[#F2D488] hover:text-[#F7DE9B] font-semibold hover:underline transition-colors inline-flex items-center gap-1 cursor-pointer"
              >
                {t('signup.signInLink', 'Sign In →')}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default SignupPage;
