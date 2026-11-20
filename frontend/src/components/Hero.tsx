import React, { useState, useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { User, ChevronRight } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { GoldLanguageSwitch } from './GoldLanguageSwitch';

interface HeroProps {
  onLoginClick?: () => void;
  isLoggedIn?: boolean;
}

export function Hero({ onLoginClick, isLoggedIn }: HeroProps) {
  const { t } = useLanguage();

  // Mouse position for smooth parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth springs for buttery cursor parallax
  const springConfig = { damping: 25, stiffness: 120 };
  const smoothMouseX = useSpring(mouseX, springConfig);
  const smoothMouseY = useSpring(mouseY, springConfig);

  // Parallax transforms for courthouse (bottom-left)
  const courthouseX = useTransform(smoothMouseX, [-1, 1], [-14, 14]);
  const courthouseY = useTransform(smoothMouseY, [-1, 1], [-8, 8]);

  // Parallax transforms for law books (bottom-right)
  const booksX = useTransform(smoothMouseX, [-1, 1], [14, -14]);
  const booksY = useTransform(smoothMouseY, [-1, 1], [10, -10]);

  // Subtle counter-parallax for hero scales
  const scalesX = useTransform(smoothMouseX, [-1, 1], [8, -8]);
  const scalesY = useTransform(smoothMouseY, [-1, 1], [6, -6]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { clientWidth, clientHeight } = e.currentTarget;
    const x = (e.clientX / clientWidth) * 2 - 1;
    const y = (e.clientY / clientHeight) * 2 - 1;
    mouseX.set(x);
    mouseY.set(y);
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      className="relative w-screen h-screen overflow-hidden bg-[#050505] text-white flex items-center justify-center select-none"
      style={{
        background: 'radial-gradient(circle at 62% 50%, #0F0D09 0%, #080808 45%, #050505 100%)',
      }}
    >
      {/* =========================================================================
          BACKGROUND TEXTURE & VIGNETTE
          ========================================================================= */}
      {/* Subtle Dark Paper Noise Filter */}
      <svg className="pointer-events-none fixed inset-0 w-full h-full opacity-[0.035] z-[1]">
        <filter id="noiseFilter">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noiseFilter)" />
      </svg>

      {/* Soft Vignette toward edges */}
      <div
        className="pointer-events-none absolute inset-0 z-[2]"
        style={{
          background: 'radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(3, 3, 3, 0.6) 75%, rgba(0, 0, 0, 0.95) 100%)',
        }}
      />

      {/* Global SVG Gradients & Glow Filters */}
      <svg className="absolute w-0 h-0" aria-hidden="true" focusable="false">
        <defs>
          <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F7DE9B" />
            <stop offset="45%" stopColor="#D9A441" />
            <stop offset="80%" stopColor="#A8731F" />
            <stop offset="100%" stopColor="#6B4410" />
          </linearGradient>

          <linearGradient id="goldHorizontal" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#F7DE9B" />
            <stop offset="50%" stopColor="#D9A441" />
            <stop offset="100%" stopColor="#A8731F" />
          </linearGradient>

          <linearGradient id="whiteCream" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="60%" stopColor="#FAF7F0" />
            <stop offset="100%" stopColor="#E2DAC7" />
          </linearGradient>

          <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="intenseGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="14" result="blur2" />
            <feMerge>
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>

      {/* =========================================================================
          DECORATIVE ELEMENT: TOP-LEFT GLOWING GOLD RIBBON WITH LENS FLARE
          ========================================================================= */}
      <div className="absolute top-0 left-0 w-[360px] sm:w-[480px] lg:w-[620px] h-[280px] sm:h-[360px] pointer-events-none z-[4] overflow-visible">
        <svg
          viewBox="0 0 600 360"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full overflow-visible"
        >
          {/* Outer diffused glow path */}
          <motion.path
            d="M-50,20 C140,25 240,110 320,130 C410,150 490,90 560,30"
            stroke="url(#goldGradient)"
            strokeWidth="8"
            strokeLinecap="round"
            opacity="0.25"
            filter="url(#intenseGlow)"
            animate={{ opacity: [0.2, 0.35, 0.2] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Main crisp ribbon line */}
          <motion.path
            d="M-50,20 C140,25 240,110 320,130 C410,150 490,90 560,30"
            stroke="url(#goldGradient)"
            strokeWidth="2.5"
            strokeLinecap="round"
            filter="url(#goldGlow)"
            animate={{ opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Secondary thin accent echo trail */}
          <path
            d="M-40,40 C150,45 250,125 330,145 C410,165 480,115 540,60"
            stroke="url(#goldGradient)"
            strokeWidth="1"
            strokeDasharray="4 6"
            opacity="0.35"
          />

          {/* Lens flare sparkle at the crest of the ribbon curve (around x=320, y=130) */}
          <g transform="translate(320, 130)">
            <motion.circle
              r="4"
              fill="#FFFFFF"
              filter="url(#intenseGlow)"
              animate={{ scale: [1, 1.4, 1], opacity: [0.85, 1, 0.85] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.path
              d="M0,-24 L2,-4 L24,0 L2,4 L0,24 L-2,4 L-24,0 L-2,-4 Z"
              fill="url(#goldGradient)"
              filter="url(#goldGlow)"
              animate={{ scale: [0.9, 1.25, 0.9], rotate: [0, 90, 180] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
            />
          </g>
        </svg>
      </div>

      {/* =========================================================================
          DECORATIVE ELEMENT: BOTTOM-RIGHT GOLD RIBBON SWOOSH CURVING UPWARD
          ========================================================================= */}
      <div className="absolute bottom-0 right-0 w-[360px] sm:w-[480px] lg:w-[600px] h-[260px] sm:h-[340px] pointer-events-none z-[4] overflow-visible">
        <svg
          viewBox="0 0 600 340"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full overflow-visible"
        >
          {/* Diffused outer glow path */}
          <motion.path
            d="M40,330 C120,280 220,220 310,210 C410,200 500,240 650,220"
            stroke="url(#goldGradient)"
            strokeWidth="7"
            strokeLinecap="round"
            opacity="0.22"
            filter="url(#intenseGlow)"
            animate={{ opacity: [0.18, 0.32, 0.18] }}
            transition={{ duration: 4.8, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Main crisp ribbon line */}
          <motion.path
            d="M40,330 C120,280 220,220 310,210 C410,200 500,240 650,220"
            stroke="url(#goldGradient)"
            strokeWidth="2"
            strokeLinecap="round"
            filter="url(#goldGlow)"
            animate={{ opacity: [0.75, 1, 0.75] }}
            transition={{ duration: 3.8, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Lens flare point along the curve at x=310, y=210 */}
          <g transform="translate(310, 210)">
            <motion.circle
              r="3.5"
              fill="#FFFFFF"
              filter="url(#intenseGlow)"
              animate={{ scale: [1, 1.35, 1], opacity: [0.75, 1, 0.75] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
            />
            <motion.path
              d="M0,-20 L2,-3 L20,0 L2,3 L0,20 L-2,3 L-20,0 L-2,-3 Z"
              fill="url(#goldGradient)"
              filter="url(#goldGlow)"
              animate={{ scale: [0.85, 1.2, 0.85], rotate: [0, -90, -180] }}
              transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
            />
          </g>
        </svg>
      </div>

      {/* =========================================================================
          DECORATIVE ELEMENT: BOTTOM-LEFT COURTHOUSE (DIM, SEPIA/CHARCOAL)
          ========================================================================= */}
      <motion.div
        style={{ x: courthouseX, y: courthouseY }}
        className="absolute -bottom-6 -left-6 sm:bottom-0 sm:left-0 w-[300px] sm:w-[420px] md:w-[500px] lg:w-[560px] pointer-events-none z-[3] opacity-20 sm:opacity-25 transition-opacity duration-300"
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

      {/* =========================================================================
          DECORATIVE ELEMENT: BOTTOM-RIGHT LAW BOOKS (DIMLY LIT LEATHER & GOLD)
          ========================================================================= */}
      <motion.div
        style={{ x: booksX, y: booksY }}
        className="absolute -bottom-8 -right-8 sm:bottom-0 sm:right-2 w-[260px] sm:w-[360px] md:w-[420px] lg:w-[460px] pointer-events-none z-[3] opacity-35 sm:opacity-40 transition-opacity duration-300"
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
            className="w-full h-auto object-contain filter contrast-[115%] brightness-[90%]"
          />
        </div>
      </motion.div>

      {/* =========================================================================
          MAIN 16:9 RESPONSIVE STAGE CONTAINER
          ========================================================================= */}
      <div className="relative w-full max-w-[1920px] h-full max-h-[1080px] px-6 sm:px-12 md:px-16 lg:px-20 flex items-center justify-between z-[10]">
        {/* =====================================================================
            ZONE 1: TOP-RIGHT LANGUAGE SWITCH & LOGIN BUTTON
            ===================================================================== */}
        <div className="absolute top-6 sm:top-8 right-6 sm:right-10 md:right-14 z-50 flex items-center gap-3">
          <GoldLanguageSwitch />

          <motion.button
            whileHover={{ y: -2, scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onLoginClick}
            className="group relative inline-flex items-center gap-2.5 px-5 sm:px-6 py-2.5 rounded-full border border-[#D9A441]/80 hover:border-[#F7DE9B] bg-[#0A0A0A]/85 hover:bg-[#14120D] backdrop-blur-md shadow-[0_0_15px_rgba(217,164,65,0.18)] hover:shadow-[0_0_28px_rgba(217,164,65,0.45)] transition-all duration-300 cursor-pointer"
          >
            {/* Subtle inner gold shimmer line on top */}
            <span className="absolute inset-x-3 top-0 h-[1px] bg-gradient-to-r from-transparent via-[#F7DE9B]/60 to-transparent" />

            {/* Gold User Icon */}
            <span className="flex items-center justify-center w-5 h-5 text-[#D9A441] group-hover:text-[#F7DE9B] transition-colors duration-200">
              <User className="w-4 h-4" strokeWidth={2.2} />
            </span>

            {/* "Login" text in crisp white */}
            <span className="font-sans font-medium text-xs sm:text-sm text-white tracking-wide group-hover:text-white/95">
              {isLoggedIn ? t('common.dashboard', 'Dashboard') : t('common.login', 'Login')}
            </span>

            {/* Small gold chevron ">" */}
            <span className="flex items-center justify-center text-[#D9A441] group-hover:text-[#F7DE9B] transition-transform duration-200 group-hover:translate-x-0.5">
              <ChevronRight className="w-4 h-4" strokeWidth={2.4} />
            </span>
          </motion.button>
        </div>

        {/* =====================================================================
            ZONE 2: LEFT SIDE BRAND BLOCK (~35% width, vertically centered)
            ===================================================================== */}
        <div className="w-full sm:w-[85%] md:w-[50%] lg:w-[38%] max-w-xl flex flex-col items-start justify-center z-20 pt-4 sm:pt-0">
          {/* Logo Emblem: Gold balance scale on classical column with stepped base, flame finial, laurel wreath */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="mb-5 sm:mb-6"
          >
            <div className="relative group cursor-pointer">
              {/* Subtle back ambient glow */}
              <div className="absolute -inset-2 rounded-full bg-[#D9A441]/15 blur-xl opacity-75 group-hover:opacity-100 transition-opacity" />

              <svg
                width="84"
                height="84"
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-16 h-16 sm:w-20 sm:h-20 drop-shadow-[0_4px_16px_rgba(217,164,65,0.35)]"
              >
                {/* Stepped Pedestal Base */}
                <rect x="36" y="86" width="28" height="3.5" rx="1" fill="url(#goldGradient)" />
                <rect x="39" y="82.5" width="22" height="3.5" rx="0.8" fill="url(#goldGradient)" />
                <rect x="42" y="79" width="16" height="3.5" rx="0.5" fill="url(#goldGradient)" />

                {/* Classical Fluted Column Shaft */}
                <path d="M44,48 L44,79 L56,79 L56,48 Z" fill="url(#goldGradient)" />
                <line x1="47" y1="49" x2="47" y2="78" stroke="#6B4410" strokeWidth="0.8" opacity="0.65" />
                <line x1="50" y1="49" x2="50" y2="78" stroke="#F7DE9B" strokeWidth="0.8" opacity="0.85" />
                <line x1="53" y1="49" x2="53" y2="78" stroke="#6B4410" strokeWidth="0.8" opacity="0.65" />

                {/* Column Capital / Pediment Top */}
                <path d="M41,45 L59,45 L56,48 L44,48 Z" fill="url(#goldGradient)" />
                <rect x="40" y="42.5" width="20" height="2.5" rx="0.8" fill="url(#goldGradient)" />

                {/* Scales Crossbeam on column top */}
                <path
                  d="M26,38 C34,35 44,34 50,34 C56,34 66,35 74,38"
                  stroke="url(#goldGradient)"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                />

                {/* Center Scales Post & Hub */}
                <line x1="50" y1="34" x2="50" y2="42.5" stroke="url(#goldGradient)" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="50" cy="34" r="2.5" fill="url(#goldGradient)" />

                {/* Flame Finial Crowning Top */}
                <path
                  d="M50,25 C52.5,29 53,30.5 50,33.5 C47,30.5 47.5,29 50,25 Z"
                  fill="url(#goldGradient)"
                  filter="url(#goldGlow)"
                />
                <circle cx="50" cy="27" r="1.2" fill="#FFFFFF" opacity="0.9" />

                {/* Left Scale Pan & Cords */}
                <line x1="26" y1="38" x2="20" y2="52" stroke="url(#goldGradient)" strokeWidth="1" opacity="0.85" />
                <line x1="26" y1="38" x2="32" y2="52" stroke="url(#goldGradient)" strokeWidth="1" opacity="0.85" />
                <path d="M18,52 C20,58 32,58 34,52 Z" fill="url(#goldGradient)" />

                {/* Right Scale Pan & Cords */}
                <line x1="74" y1="38" x2="68" y2="52" stroke="url(#goldGradient)" strokeWidth="1" opacity="0.85" />
                <line x1="74" y1="38" x2="80" y2="52" stroke="url(#goldGradient)" strokeWidth="1" opacity="0.85" />
                <path d="M66,52 C68,58 80,58 82,52 Z" fill="url(#goldGradient)" />

                {/* Laurel Wreath Curving on Left Side */}
                <g fill="url(#goldGradient)" opacity="0.9">
                  {/* Left Wreath Stem */}
                  <path
                    d="M42,88 C26,84 14,68 14,48 C14,34 22,22 34,16"
                    stroke="url(#goldGradient)"
                    strokeWidth="1.2"
                    fill="none"
                    strokeLinecap="round"
                  />
                  {/* Left Leaves */}
                  <path d="M35,16 C30,15 28,19 33,21 C37,22 38,18 35,16 Z" />
                  <path d="M26,22 C21,22 20,27 25,28 C29,29 30,24 26,22 Z" />
                  <path d="M19,31 C14,32 14,37 19,38 C23,38 23,33 19,31 Z" />
                  <path d="M15,42 C10,44 11,49 16,49 C20,49 20,44 15,42 Z" />
                  <path d="M14,54 C10,57 12,62 17,61 C21,60 20,55 14,54 Z" />
                  <path d="M17,66 C14,70 17,74 22,72 C26,70 24,65 17,66 Z" />
                  <path d="M24,77 C22,81 26,84 30,81 C34,78 31,74 24,77 Z" />
                  <path d="M33,84 C32,88 37,90 40,86 C43,82 39,79 33,84 Z" />
                </g>

                {/* Laurel Wreath Curving on Right Side */}
                <g fill="url(#goldGradient)" opacity="0.9">
                  {/* Right Wreath Stem */}
                  <path
                    d="M58,88 C74,84 86,68 86,48 C86,34 78,22 66,16"
                    stroke="url(#goldGradient)"
                    strokeWidth="1.2"
                    fill="none"
                    strokeLinecap="round"
                  />
                  {/* Right Leaves */}
                  <path d="M65,16 C70,15 72,19 67,21 C63,22 62,18 65,16 Z" />
                  <path d="M74,22 C79,22 80,27 75,28 C71,29 70,24 74,22 Z" />
                  <path d="M81,31 C86,32 86,37 81,38 C77,38 77,33 81,31 Z" />
                  <path d="M85,42 C90,44 89,49 84,49 C80,49 80,44 85,42 Z" />
                  <path d="M86,54 C90,57 88,62 83,61 C79,60 80,55 86,54 Z" />
                  <path d="M83,66 C86,70 83,74 78,72 C74,70 76,65 83,66 Z" />
                  <path d="M76,77 C78,81 74,84 70,81 C66,78 69,74 76,77 Z" />
                  <path d="M67,84 C68,88 63,90 60,86 C57,82 61,79 67,84 Z" />
                </g>
              </svg>
            </div>
          </motion.div>

          {/* Title: "Law Mithra" */}
          <motion.div
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.15, ease: 'easeOut' }}
            className="relative"
          >
            <h1 className="font-serif font-bold text-5xl sm:text-6xl md:text-7xl lg:text-[5.4rem] tracking-tight leading-[0.92] flex items-baseline">
              {/* "Law" in white-to-cream gradient */}
              <span className="bg-gradient-to-b from-[#FFFFFF] via-[#FAF7F0] to-[#DDD2BE] bg-clip-text text-transparent drop-shadow-[0_2px_14px_rgba(255,255,255,0.18)]">
                Law
              </span>
              {/* "Mithra" in bright gold gradient */}
              <span className="ml-3 sm:ml-4 bg-gradient-to-r from-[#F7DE9B] via-[#D9A441] to-[#A8731F] bg-clip-text text-transparent drop-shadow-[0_4px_24px_rgba(217,164,65,0.38)]">
                Mithra
              </span>
            </h1>

            {/* Thin gold curved swoosh underline */}
            <div className="w-full mt-2 sm:mt-3 overflow-visible">
              <svg
                viewBox="0 0 420 18"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full max-w-[360px] sm:max-w-[420px] h-3.5 sm:h-4 overflow-visible"
              >
                <path
                  d="M4,12 C110,3 280,2 416,14"
                  stroke="url(#goldHorizontal)"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  filter="url(#goldGlow)"
                />
                <path
                  d="M40,11 C130,5 260,4 380,13"
                  stroke="#FFFFFF"
                  strokeWidth="0.8"
                  strokeLinecap="round"
                  opacity="0.6"
                />
              </svg>
            </div>
          </motion.div>

          {/* Subtitle: "Your Smart Legal Assistant" */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: 'easeOut' }}
            className="mt-4 sm:mt-5"
          >
            <p className="font-sans font-medium text-xs sm:text-sm md:text-base tracking-[0.24em] sm:tracking-[0.28em] uppercase text-white/90">
              Your Smart{' '}
              <span className="font-bold bg-gradient-to-r from-[#F7DE9B] via-[#D9A441] to-[#A8731F] bg-clip-text text-transparent drop-shadow-[0_0_12px_rgba(217,164,65,0.3)]">
                Legal
              </span>{' '}
              Assistant
            </p>
          </motion.div>

          {/* Thin gold divider line with small gold diamond/sparkle in the center */}
          <motion.div
            initial={{ opacity: 0, scaleX: 0.6 }}
            animate={{ opacity: 1, scaleX: 1 }}
            transition={{ duration: 0.65, delay: 0.42, ease: 'easeOut' }}
            className="flex items-center justify-start my-4 sm:my-5 w-48 sm:w-64"
          >
            {/* Left line */}
            <span className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#D9A441]/80 to-[#D9A441]" />

            {/* Center gold diamond sparkle */}
            <span className="mx-2.5 flex items-center justify-center">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="overflow-visible">
                <path
                  d="M6,0 L7.5,4.5 L12,6 L7.5,7.5 L6,12 L4.5,7.5 L0,6 L4.5,4.5 Z"
                  fill="url(#goldGradient)"
                  filter="url(#goldGlow)"
                />
                <circle cx="6" cy="6" r="1.5" fill="#FFFFFF" />
              </svg>
            </span>

            {/* Right line */}
            <span className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[#D9A441]/80 to-[#D9A441]" />
          </motion.div>

          {/* Tagline: "in Every Indian Language" */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.52, ease: 'easeOut' }}
            className="flex items-center gap-3"
          >
            <span className="h-[1px] w-5 sm:w-8 bg-gradient-to-r from-transparent to-[#D9A441]/70" />
            <span className="font-serif italic text-xs sm:text-sm text-[#B9AE9A] tracking-wider">
              {t('brand.languageScope', 'in Every Indian Language')}
            </span>
            <span className="h-[1px] w-5 sm:w-8 bg-gradient-to-l from-transparent to-[#D9A441]/70" />
          </motion.div>

          {/* Primary Call-to-Action Button */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.62, ease: 'easeOut' }}
            className="mt-6 sm:mt-7 flex items-center gap-3.5 z-30"
          >
            <motion.button
              whileHover={{ y: -2, scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onLoginClick}
              className="group relative inline-flex items-center gap-2.5 px-6 sm:px-7 py-3 sm:py-3.5 rounded-full bg-gradient-to-r from-[#C9953A] via-[#F2D488] to-[#C9953A] text-[#111] font-sans font-bold text-sm sm:text-base shadow-[0_0_24px_rgba(217,164,65,0.35)] hover:shadow-[0_0_35px_rgba(242,212,136,0.55)] transition-all duration-300 cursor-pointer"
            >
              <span>{isLoggedIn ? t('common.dashboard', 'Open Legal Dashboard') : t('hero.consultAI', 'Consult Legal AI')}</span>
              <ChevronRight className="w-4 h-4 stroke-[2.5] text-[#111] group-hover:translate-x-1 transition-transform" />
            </motion.button>
          </motion.div>
        </div>

        {/* =====================================================================
            ZONE 3: CENTER-RIGHT HERO VISUAL (~62% width center)
            ===================================================================== */}
        <div className="absolute left-[46%] sm:left-[50%] md:left-[56%] lg:left-[60%] top-1/2 -translate-y-1/2 -translate-x-1/2 w-[340px] sm:w-[480px] md:w-[580px] lg:w-[680px] h-[340px] sm:h-[480px] md:h-[580px] lg:h-[680px] flex items-center justify-center pointer-events-none z-10">
          {/* Radial Warm Gold Glow behind the visual */}
          <div
            className="absolute inset-0 rounded-full pointer-events-none"
            style={{
              background: 'radial-gradient(circle at 50% 50%, rgba(217, 164, 65, 0.24) 0%, rgba(168, 115, 31, 0.09) 45%, rgba(0, 0, 0, 0) 72%)',
            }}
          />

          {/* Concentric Thin Gold Circles Container (slow rotation/breathing) */}
          <div className="absolute inset-0 flex items-center justify-center">
            {/* Outer Concentric Circle (1px stroke, opacity 0.15) */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 120, repeat: Infinity, ease: 'linear' }}
              className="absolute w-[88%] h-[88%] rounded-full border border-[#D9A441]/20 shadow-[0_0_30px_rgba(217,164,65,0.06)]"
            />

            {/* Middle Concentric Circle (1px stroke, opacity 0.28) */}
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 90, repeat: Infinity, ease: 'linear' }}
              className="absolute w-[74%] h-[74%] rounded-full border border-[#D9A441]/35 border-dashed"
            />

            {/* Inner Concentric Circle (1px stroke, opacity 0.45) */}
            <motion.div
              animate={{ scale: [1, 1.02, 1] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute w-[58%] h-[58%] rounded-full border border-[#F7DE9B]/40 shadow-[0_0_25px_rgba(217,164,65,0.12)]"
            />

            {/* Horizontal Light Streaks extending Left and Right from outer ring */}
            {/* Left streak */}
            <div className="absolute left-[-16%] sm:left-[-22%] top-1/2 -translate-y-1/2 flex items-center">
              <span className="w-2 h-2 rounded-full bg-[#FFFFFF] shadow-[0_0_12px_#F7DE9B] ring-2 ring-[#D9A441]" />
              <span className="h-[1.5px] w-24 sm:w-36 md:w-44 bg-gradient-to-r from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
            </div>

            {/* Right streak */}
            <div className="absolute right-[-16%] sm:right-[-22%] top-1/2 -translate-y-1/2 flex items-center">
              <span className="h-[1.5px] w-24 sm:w-36 md:w-44 bg-gradient-to-l from-[#FFFFFF] via-[#D9A441] to-transparent shadow-[0_0_8px_rgba(217,164,65,0.5)]" />
              <span className="w-2 h-2 rounded-full bg-[#FFFFFF] shadow-[0_0_12px_#F7DE9B] ring-2 ring-[#D9A441]" />
            </div>

            {/* Four 4-point star-shaped light flares at Top, Bottom, Left, and Right of outer ring */}
            {/* Top Star Flare */}
            <motion.div
              animate={{ scale: [0.95, 1.3, 0.95], opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute top-[6%] left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="overflow-visible">
                <path
                  d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                  fill="url(#goldGradient)"
                  filter="url(#intenseGlow)"
                />
                <circle cx="12" cy="12" r="2.5" fill="#FFFFFF" />
              </svg>
            </motion.div>

            {/* Bottom Star Flare */}
            <motion.div
              animate={{ scale: [0.95, 1.3, 0.95], opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 2.8, delay: 1.4, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute bottom-[6%] left-1/2 -translate-x-1/2 translate-y-1/2 flex items-center justify-center"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="overflow-visible">
                <path
                  d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                  fill="url(#goldGradient)"
                  filter="url(#intenseGlow)"
                />
                <circle cx="12" cy="12" r="2.5" fill="#FFFFFF" />
              </svg>
            </motion.div>

            {/* Left Star Flare */}
            <motion.div
              animate={{ scale: [0.95, 1.3, 0.95], opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 2.8, delay: 0.7, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute left-[6%] top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="overflow-visible">
                <path
                  d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                  fill="url(#goldGradient)"
                  filter="url(#intenseGlow)"
                />
                <circle cx="12" cy="12" r="2.5" fill="#FFFFFF" />
              </svg>
            </motion.div>

            {/* Right Star Flare */}
            <motion.div
              animate={{ scale: [0.95, 1.3, 0.95], opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 2.8, delay: 2.1, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute right-[6%] top-1/2 translate-x-1/2 -translate-y-1/2 flex items-center justify-center"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="overflow-visible">
                <path
                  d="M12,0 L14,9 L24,12 L14,15 L12,24 L10,15 L0,12 L10,9 Z"
                  fill="url(#goldGradient)"
                  filter="url(#intenseGlow)"
                />
                <circle cx="12" cy="12" r="2.5" fill="#FFFFFF" />
              </svg>
            </motion.div>
          </div>

          {/* Ornate Antique Scales of Justice (Floating 4s loop) */}
          <motion.div
            style={{ x: scalesX, y: scalesY }}
            animate={{ y: [-10, 10, -10] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            className="relative w-[75%] sm:w-[82%] md:w-[86%] max-w-[560px] h-auto z-20 drop-shadow-[0_12px_45px_rgba(217,164,65,0.42)]"
          >
            {/* Warm Gold Rim Light Aura */}
            <div className="absolute inset-4 rounded-full bg-[#D9A441]/20 blur-2xl pointer-events-none -z-10" />

            <img
              src="/assets/scales-of-justice.png"
              alt="Ornate Scales of Justice"
              className="w-full h-auto object-contain filter contrast-[112%] brightness-[105%]"
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
