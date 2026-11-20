/**
 * ComplaintReportView.tsx
 * Universal Complaint Analysis Report — full 7-section premium UI.
 * Matches Law Mithra dark gold design. Integrates with the backend report API.
 */

import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Scale, AlertTriangle, CheckCircle2, XCircle,
  User, BookOpen, Shield, Gavel, Printer, Sparkles,
  RefreshCw, Clock, Download, ChevronDown, ChevronUp,
  Info, History, Loader2,
} from 'lucide-react';
import { ComplaintReport, ReportListResponse, downloadReportPDF } from '@/lib/api';
import { useToast } from '@/components/ui/Toast';

// ── Colour helpers ─────────────────────────────────────────────────────────────
const GOLD   = '#D9A441';
const GOLD_H = '#F7DE9B';
const GOLD_D = '#A8731F';
const BG     = '#050505';
const BORDER = 'rgba(217,164,65,0.22)';

// ── Tiny helpers ───────────────────────────────────────────────────────────────
function isBlank(v: string) {
  return !v || v === 'Not provided' || v === 'Requires verification' || v === 'Not Applicable';
}

function Cell({ label, value, wide }: { label: string; value: string; wide?: boolean }) {
  return (
    <div
      className={`p-2.5 ${wide ? 'col-span-2' : ''}`}
      style={{ background: 'rgba(8,8,8,0.9)', borderRight: BORDER, borderBottom: `1px solid ${BORDER}` }}
    >
      <p className="text-[8.5px] font-bold uppercase tracking-widest mb-1" style={{ color: GOLD_D, fontFamily: 'Inter, sans-serif' }}>
        {label}
      </p>
      <p className={`text-[11px] leading-snug font-sans ${isBlank(value) ? 'text-[#4a4a4a] italic' : 'text-[#EDEDED]'}`}>
        {value || 'Not provided'}
      </p>
    </div>
  );
}

function SecHeader({ n, title }: { n: number; title: string }) {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2"
      style={{ background: 'linear-gradient(90deg,rgba(80,45,10,0.95) 0%,rgba(15,10,3,0) 100%)', borderLeft: `3px solid ${GOLD}` }}
    >
      <span className="text-[9px] font-black" style={{ color: GOLD }}>{n}.</span>
      <h3 className="text-[10px] font-black uppercase tracking-[0.14em] font-sans" style={{ color: GOLD_H }}>{title}</h3>
    </div>
  );
}

function EvList({ items, type }: { items: string[]; type: 'ok' | 'missing' }) {
  if (!items?.length) return <p className="text-[10px] italic text-[#4a4a4a] font-sans">Not provided</p>;
  return (
    <ul className="space-y-1">
      {items.map((it, i) => (
        <li key={i} className="flex items-start gap-1.5 text-[10.5px] font-sans">
          {type === 'ok'
            ? <CheckCircle2 className="w-3 h-3 shrink-0 mt-0.5" style={{ color: GOLD }} />
            : <XCircle className="w-3 h-3 shrink-0 mt-0.5 text-[#8A4A20]" />}
          <span className={isBlank(it) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}>{it}</span>
        </li>
      ))}
    </ul>
  );
}

// ── Props ──────────────────────────────────────────────────────────────────────
export interface ComplaintReportViewProps {
  report: ComplaintReport | null;
  reportList: ReportListResponse | null;
  documentId: string;
  isLoading: boolean;
  isLoadingList: boolean;
  error: string | null;
  onGenerate: () => void;
  onSelectVersion: (r: ComplaintReport) => void;
}

// ── Main Component ─────────────────────────────────────────────────────────────
export function ComplaintReportView({
  report,
  reportList,
  documentId,
  isLoading,
  isLoadingList,
  error,
  onGenerate,
  onSelectVersion,
}: ComplaintReportViewProps) {
  const { addToast } = useToast();
  const printRef = useRef<HTMLDivElement>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // ── PDF download (via authenticated API) ────────────────────────────────────
  const handleDownloadPDF = async () => {
    if (!report?.id) return;
    setDownloading(true);
    try {
      await downloadReportPDF(documentId, report.id);
      addToast({
        title: 'PDF Downloaded',
        description: `Law Mithra complaint report (${report.report_id}) downloaded.`,
        variant: 'success',
      });
    } catch (err: any) {
      addToast({
        title: 'Download Failed',
        description: err.message || 'Could not download PDF report.',
        variant: 'destructive',
      });
    } finally {
      setDownloading(false);
    }
  };

  // ── Print (browser) ─────────────────────────────────────────────────────────
  const handlePrint = () => {
    if (!printRef.current) return;
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`<html><head>
      <title>Law Mithra — ${report?.report_id}</title>
      <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:Arial,sans-serif;font-size:10px;color:#111;background:#fff;padding:12mm}
        h1{font-size:14px;text-align:center;letter-spacing:3px;color:#0F1B35;margin-bottom:2px}
        h2{font-size:8px;text-align:center;color:#555;letter-spacing:2px;margin-bottom:8px}
        .sec{background:#1A2847;color:#fff;padding:3px 7px;font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin:6px 0 2px}
        table{width:100%;border-collapse:collapse;margin-bottom:3px}
        th{background:#E8EEF7;font-size:7.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;padding:3px 5px;border:0.4px solid #C0C8D8;color:#0F1B35}
        td{font-size:9px;padding:3px 5px;border:0.4px solid #C0C8D8;vertical-align:top;line-height:1.4}
        .disc{color:#CC3300;font-size:8px;margin-top:8px;line-height:1.4}
        .conf{color:#888;font-size:7px;text-align:center;margin-top:4px;font-style:italic}
        hr{border:none;border-top:1px solid #C0C8D8;margin:6px 0}
      </style></head><body>
      <h1>LAW MITHRA</h1>
      <h2>YOUR SMART LEGAL ASSISTANT &nbsp;|&nbsp; UNIVERSAL COMPLAINT REPORT</h2>
      ${printRef.current.innerHTML}
      <hr/>
      <p class="disc"><strong>IMPORTANT:</strong> AI-assisted information only; not a police finding, court decision or substitute for a qualified advocate. Allegations are not proven facts. Legal provisions and deadlines must be verified against authoritative, current sources and the incident date.</p>
      <p class="conf">CONFIDENTIAL — Contains personal and potentially sensitive case information. Share only with authorised people.</p>
    </body></html>`);
    win.document.close();
    win.print();
  };

  // ── Empty state ─────────────────────────────────────────────────────────────
  if (!report && !isLoading && !error) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16 px-6 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative mb-8"
        >
          <div className="w-28 h-28 rounded-full flex items-center justify-center mx-auto"
            style={{ background: 'radial-gradient(circle,rgba(168,115,31,0.14) 0%,transparent 70%)', border: `1px solid ${BORDER}` }}>
            <FileText className="w-12 h-12" style={{ color: GOLD }} />
          </div>
          {[0,1,2].map(i => (
            <motion.div key={i} className="absolute w-2 h-2 rounded-full"
              style={{ background: GOLD, top:`${[8,55,85][i]}%`, left:`${[80,96,72][i]}%` }}
              animate={{ opacity:[0.3,1,0.3], scale:[0.8,1.3,0.8] }}
              transition={{ duration:2.2, delay:i*0.4, repeat:Infinity }} />
          ))}
        </motion.div>

        <h3 className="text-lg font-bold mb-2 font-sans" style={{ color: GOLD_H }}>
          Generate Complaint Analysis Report
        </h3>
        <p className="text-[#8A8A8A] text-sm font-sans max-w-sm mb-2 leading-relaxed">
          Law Mithra AI will analyse the uploaded document and generate a structured
          7-section legal report — identifying parties, applicable law, evidence, and next steps.
        </p>
        <p className="text-[#5a5a5a] text-[11px] font-sans mb-8">
          Works with: FIR, Complaint, Court Order, Legal Notice, Property Dispute, Cybercrime, Fraud, Family matters
        </p>

        <motion.button whileHover={{ scale:1.03, y:-2 }} whileTap={{ scale:0.97 }}
          onClick={onGenerate}
          className="flex items-center gap-3 px-8 py-3.5 rounded-[14px] text-white font-semibold text-sm font-sans"
          style={{ background:'linear-gradient(135deg,#5C4420 0%,#8A6A2E 50%,#4A3618 100%)', border:`1px solid rgba(217,164,65,0.6)`, boxShadow:`0 0 24px rgba(168,115,31,0.25)` }}>
          <Sparkles className="w-4 h-4" style={{ color: GOLD_H }} />
          Generate Report
        </motion.button>

        <p className="text-[9px] mt-4 font-sans" style={{ color: '#3a3a3a' }}>
          Powered by Gemini AI · Indian Law · Analysis only — not legal advice
        </p>
      </div>
    );
  }

  // ── Loading state ───────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 px-6 text-center">
        <motion.div animate={{ rotate:360 }} transition={{ duration:2.5, repeat:Infinity, ease:'linear' }} className="mb-6">
          <Scale className="w-14 h-14" style={{ color: GOLD }} />
        </motion.div>
        <h3 className="text-base font-semibold font-sans mb-2" style={{ color: GOLD_H }}>Analysing Document…</h3>
        <p className="text-[#8A8A8A] text-xs font-sans max-w-xs leading-relaxed">
          Law Mithra is reading the document, identifying parties, applicable Indian law sections,
          and generating the 7-section report. This may take 15–30 seconds.
        </p>
        <div className="flex gap-2 mt-7">
          {[0,1,2,3].map(i => (
            <motion.div key={i} className="w-2 h-2 rounded-full" style={{ background: GOLD }}
              animate={{ opacity:[0.2,1,0.2], y:[0,-6,0] }}
              transition={{ duration:1.3, delay:i*0.2, repeat:Infinity }} />
          ))}
        </div>
        <div className="mt-6 text-[10px] font-sans space-y-1" style={{ color:'#3a3a3a' }}>
          {['Extracting text from document…','Identifying parties and facts…','Matching applicable Indian law…','Preparing 7-section report…'].map((s,i) => (
            <motion.p key={i} initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:i*4, duration:1 }}>{s}</motion.p>
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ─────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20 px-6 text-center">
        <div className="w-16 h-16 rounded-full flex items-center justify-center mb-5"
          style={{ background:'rgba(168,50,30,0.14)', border:'1px solid rgba(220,80,60,0.4)' }}>
          <AlertTriangle className="w-7 h-7 text-red-400" />
        </div>
        <h3 className="text-base font-semibold text-red-400 font-sans mb-2">Report Generation Failed</h3>
        <p className="text-[#8A8A8A] text-xs font-sans max-w-sm mb-6 leading-relaxed">{error}</p>
        <button onClick={onGenerate}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold font-sans"
          style={{ border:`1px solid rgba(217,164,65,0.4)`, background:'rgba(90,52,20,0.4)', color: GOLD_H }}>
          <RefreshCw className="w-4 h-4" /> Try Again
        </button>
      </div>
    );
  }

  if (!report) return null;

  // ── Report render ───────────────────────────────────────────────────────────
  return (
    <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.4 }}
      className="flex flex-col h-full" style={{ background: BG }}>

      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between px-4 py-2.5 shrink-0 gap-2 flex-wrap"
        style={{ borderBottom:`1px solid ${BORDER}` }}>
        <div className="flex items-center gap-2 flex-wrap">
          <Gavel className="w-4 h-4 shrink-0" style={{ color: GOLD }} />
          <span className="text-xs font-semibold font-sans tracking-wide" style={{ color: GOLD_H }}>
            Universal Complaint Report
          </span>
          <span className="text-[9px] px-2 py-0.5 rounded-full font-bold font-sans"
            style={{ background:'rgba(168,115,31,0.18)', color:GOLD, border:`1px solid ${BORDER}` }}>
            {report.report_id}
          </span>
          <span className="text-[9px] px-2 py-0.5 rounded-full font-sans"
            style={{ background:'rgba(60,60,60,0.5)', color:'#8A8A8A', border:'1px solid rgba(255,255,255,0.08)' }}>
            v{report.version}
          </span>
          {/* Version history toggle */}
          {(reportList?.count ?? 0) > 1 && (
            <button onClick={() => setShowHistory(h => !h)}
              className="flex items-center gap-1 text-[9px] font-sans px-2 py-0.5 rounded-full"
              style={{ border:`1px solid ${BORDER}`, color:'#8A8A8A' }}>
              <History className="w-3 h-3" />
              {reportList!.count} versions
              {showHistory ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[9px] font-sans" style={{ color:'#4a4a4a' }}>
            <Clock className="w-3 h-3 inline mr-0.5" />{report.generated_date}
          </span>
          <button onClick={onGenerate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold font-sans"
            style={{ border:`1px solid ${BORDER}`, color:GOLD, background:'rgba(90,52,20,0.2)' }}>
            <RefreshCw className="w-3 h-3" /> Regenerate
          </button>
          <button onClick={handleDownloadPDF} disabled={downloading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold font-sans cursor-pointer disabled:opacity-60"
            style={{ border:`1px solid ${BORDER}`, color:GOLD_H, background:'linear-gradient(135deg,rgba(92,68,32,0.6),rgba(74,54,24,0.6))' }}>
            {downloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
            <span>{downloading ? 'Downloading…' : 'Download PDF'}</span>
          </button>
          <button onClick={handlePrint}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold font-sans"
            style={{ border:`1px solid ${BORDER}`, color:GOLD, background:'rgba(90,52,20,0.2)' }}>
            <Printer className="w-3 h-3" /> Print
          </button>
        </div>
      </div>

      {/* ── Version History Dropdown ── */}
      <AnimatePresence>
        {showHistory && reportList && (
          <motion.div initial={{ height:0, opacity:0 }} animate={{ height:'auto', opacity:1 }} exit={{ height:0, opacity:0 }}
            className="overflow-hidden shrink-0"
            style={{ borderBottom:`1px solid ${BORDER}`, background:'rgba(10,8,3,0.95)' }}>
            <div className="px-4 py-2 flex gap-2 overflow-x-auto">
              {reportList.reports.map(r => (
                <button key={r.id} onClick={() => { onSelectVersion(r); setShowHistory(false); }}
                  className="shrink-0 flex flex-col items-start px-3 py-2 rounded-lg text-[10px] font-sans text-left"
                  style={{
                    border: r.id === report.id ? `1px solid ${GOLD}` : `1px solid ${BORDER}`,
                    background: r.id === report.id ? 'rgba(168,115,31,0.15)' : 'rgba(20,15,5,0.8)',
                    color: r.id === report.id ? GOLD_H : '#8A8A8A',
                  }}>
                  <span className="font-bold">{r.report_id} v{r.version}</span>
                  <span className="text-[9px]">{r.generated_date}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Print-only content (hidden) ── */}
      <div ref={printRef} style={{ display:'none' }}>
        {/* Identity Row */}
        <table><tbody><tr>
          <th>REPORT ID</th><th>CASE / COMPLAINT NO.</th><th>GENERATED DATE</th><th>STATUS</th>
        </tr><tr>
          <td>{report.report_id}</td><td>{report.case_complaint_no}</td>
          <td>{report.generated_date}</td><td>{report.case_status}</td>
        </tr></tbody></table>
        <div className="sec">1. CASE AT A GLANCE</div>
        <table><tbody><tr>
          <th>COMPLAINT TYPE</th><th>PARTIES INVOLVED</th><th>DATE & PLACE</th>
        </tr><tr>
          <td>{report.complaint_type}</td><td>{report.parties_involved}</td><td>{report.incident_date_place}</td>
        </tr></tbody></table>
        <div className="sec">2. COMPLAINT SUMMARY</div>
        <table><tbody><tr><td>{report.complaint_summary}</td></tr></tbody></table>
        <div className="sec">3. POSSIBLE LEGAL PROVISIONS</div>
        <table><tbody>
          <tr><th>ACT / SECTION</th><th>WHY IT MAY BE RELEVANT</th><th>VERIFICATION / CAVEAT</th></tr>
          {(report.legal_provisions||[]).map((p,i) => (
            <tr key={i}><td>{p.act_section}</td><td>{p.relevance}</td><td>{p.caveat}</td></tr>
          ))}
        </tbody></table>
        <div className="sec">4. KEY EVIDENCE & DOCUMENTS</div>
        <table><tbody>
          <tr><th>AVAILABLE MATERIAL</th><th>MISSING / TO BE VERIFIED</th></tr>
          <tr>
            <td>{(report.evidence_available||[]).map((e,i)=>`✓ ${e}`).join('\n')}</td>
            <td>{(report.evidence_missing||[]).map((e,i)=>`✗ ${e}`).join('\n')}</td>
          </tr>
        </tbody></table>
        <div className="sec">5. BALANCED CASE VIEW</div>
        <table><tbody>
          <tr><th>COMPLAINANT / APPLICANT SIDE</th><th>RESPONDENT / ACCUSED / OTHER SIDE</th></tr>
          <tr><td>{report.complainant_side}</td><td>{report.respondent_side}</td></tr>
        </tbody></table>
        <div className="sec">6. RIGHTS & NEXT STEPS</div>
        <table><tbody>
          <tr><th>PERSON'S ROLE</th><th>PRACTICAL NEXT STEPS / DEADLINES</th></tr>
          <tr><td>{report.persons_role}</td><td>{report.rights_next_steps}</td></tr>
        </tbody></table>
        <div className="sec">7. ADVOCATE REVIEW / CASE STATUS</div>
        <table><tbody>
          <tr><th>QUESTIONS FOR ADVOCATE</th><th>CURRENT STAGE</th><th>LAST UPDATED</th></tr>
          <tr>
            <td>{report.advocate_questions}</td><td>{report.current_stage}</td>
            <td>Date: {report.last_updated_date}<br/>Version: {report.version}</td>
          </tr>
        </tbody></table>
      </div>

      {/* ── Scrollable Report Body ── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5"
        style={{ background: BG, scrollbarWidth:'thin', scrollbarColor:`${GOLD_D} #0a0a0a` }}>

        {/* Header */}
        <div className="text-center pb-3" style={{ borderBottom:`1px solid ${BORDER}` }}>
          <h1 className="text-[15px] font-black tracking-[0.22em] uppercase font-sans" style={{ color: GOLD_H }}>LAW MITHRA</h1>
          <p className="text-[8px] tracking-[0.18em] uppercase mt-0.5 font-sans" style={{ color:'#8A8A8A' }}>
            Your Smart Legal Assistant &nbsp;|&nbsp; Universal Complaint Report
          </p>
          {report.document_title && (
            <p className="text-[10px] mt-1 font-sans italic" style={{ color: GOLD }}>{report.document_title}</p>
          )}
        </div>

        {/* Identity bar */}
        <div className="grid grid-cols-4 rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          {[
            ['Report ID', report.report_id],
            ['Case / Complaint No.', report.case_complaint_no],
            ['Generated Date', report.generated_date],
            ['Status', report.case_status],
          ].map(([lbl, val], i) => (
            <div key={i} className="p-2.5" style={{ borderRight: i < 3 ? `1px solid ${BORDER}` : 'none', background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8px] font-bold uppercase tracking-widest mb-1 font-sans" style={{ color: GOLD_D }}>{lbl}</p>
              <p className={`text-[11px] font-sans font-semibold ${isBlank(val) ? 'text-[#4a4a4a] italic' : 'text-[#F7DE9B]'}`}>{val || 'Not provided'}</p>
            </div>
          ))}
        </div>

        {/* Section 1 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={1} title="Case at a Glance" />
          <div className="grid grid-cols-3" style={{ borderTop:`1px solid ${BORDER}` }}>
            <Cell label="Complaint Type / Subject" value={report.complaint_type} />
            <Cell label="Parties Involved" value={report.parties_involved} />
            <div className="p-2.5" style={{ background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8.5px] font-bold uppercase tracking-widest mb-1 font-sans" style={{ color: GOLD_D }}>Date & Place</p>
              <p className={`text-[11px] font-sans ${isBlank(report.incident_date_place) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.incident_date_place || 'Not provided'}
              </p>
            </div>
          </div>
        </div>

        {/* Section 2 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={2} title="Complaint Summary" />
          <div className="p-2.5" style={{ background:'rgba(20,15,5,0.4)', borderTop:`1px solid ${BORDER}` }}>
            <p className="text-[9px] font-sans italic mb-2" style={{ color:'#5a5a5a' }}>
              Neutral summary of what the complaint/document says: who is involved, what allegedly happened,
              when and where, the impact claimed, and what action is requested. Reported claims are separated from verified facts.
            </p>
            <p className="text-[9px] font-bold uppercase tracking-widest mb-1.5 font-sans" style={{ color: GOLD_D }}>
              AI-Generated Case Summary
            </p>
            <p className={`text-[11.5px] leading-relaxed font-sans ${isBlank(report.complaint_summary) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
              {report.complaint_summary || 'Requires verification'}
            </p>
          </div>
        </div>

        {/* Section 3 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={3} title="Possible Legal Provisions" />
          <div style={{ borderTop:`1px solid ${BORDER}` }}>
            {/* Table header */}
            <div className="grid grid-cols-3 px-3 py-1.5"
              style={{ background:'rgba(80,45,10,0.3)', borderBottom:`1px solid ${BORDER}` }}>
              {['Act / Section', 'Why It May Be Relevant', 'Verification / Caveat'].map(h => (
                <p key={h} className="text-[8.5px] font-bold uppercase tracking-widest font-sans" style={{ color: GOLD }}>{h}</p>
              ))}
            </div>
            {(report.legal_provisions || []).map((p, i) => (
              <div key={i} className="grid grid-cols-3"
                style={{ borderBottom: i < (report.legal_provisions.length - 1) ? `1px solid rgba(217,164,65,0.08)` : 'none', background: i % 2 === 0 ? 'rgba(8,8,8,0.9)' : 'rgba(14,10,3,0.8)' }}>
                <div className="px-3 py-2.5" style={{ borderRight:`1px solid ${BORDER}` }}>
                  <p className="text-[11px] font-semibold font-sans" style={{ color: GOLD_H }}>{p.act_section}</p>
                </div>
                <div className="px-3 py-2.5" style={{ borderRight:`1px solid ${BORDER}` }}>
                  <p className="text-[10.5px] leading-snug font-sans text-[#EDEDED]">{p.relevance}</p>
                </div>
                <div className="px-3 py-2.5">
                  <p className="text-[10.5px] leading-snug font-sans italic text-[#8A8A8A]">{p.caveat}</p>
                </div>
              </div>
            ))}
            {(!report.legal_provisions?.length) && (
              <p className="p-3 text-[10px] italic font-sans text-[#4a4a4a]">Requires verification</p>
            )}
          </div>
        </div>

        {/* Section 4 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={4} title="Key Evidence & Documents" />
          <div className="grid grid-cols-2" style={{ borderTop:`1px solid ${BORDER}` }}>
            <div className="p-3" style={{ borderRight:`1px solid ${BORDER}`, background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8.5px] font-bold uppercase tracking-widest mb-2 font-sans" style={{ color: GOLD_D }}>Available Material</p>
              <EvList items={report.evidence_available} type="ok" />
            </div>
            <div className="p-3" style={{ background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8.5px] font-bold uppercase tracking-widest mb-2 font-sans text-[#8A4A20]">Missing / To Be Verified</p>
              <EvList items={report.evidence_missing} type="missing" />
            </div>
          </div>
        </div>

        {/* Section 5 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={5} title="Balanced Case View" />
          <div className="grid grid-cols-2" style={{ borderTop:`1px solid ${BORDER}` }}>
            <div className="p-3" style={{ borderRight:`1px solid ${BORDER}`, background:'rgba(8,8,8,0.9)' }}>
              <div className="flex items-center gap-1.5 mb-2">
                <User className="w-3 h-3" style={{ color: GOLD }} />
                <p className="text-[8.5px] font-bold uppercase tracking-widest font-sans" style={{ color: GOLD }}>Complainant / Applicant Side</p>
              </div>
              <p className={`text-[10.5px] leading-relaxed font-sans whitespace-pre-line ${isBlank(report.complainant_side) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.complainant_side || 'Requires verification'}
              </p>
            </div>
            <div className="p-3" style={{ background:'rgba(8,8,8,0.9)' }}>
              <div className="flex items-center gap-1.5 mb-2">
                <Shield className="w-3 h-3 text-[#8A8A8A]" />
                <p className="text-[8.5px] font-bold uppercase tracking-widest font-sans text-[#8A8A8A]">Respondent / Accused / Other Side</p>
              </div>
              <p className={`text-[10.5px] leading-relaxed font-sans whitespace-pre-line ${isBlank(report.respondent_side) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.respondent_side || 'Requires verification'}
              </p>
            </div>
          </div>
          <div className="px-3 py-1.5" style={{ background:'rgba(168,115,31,0.05)', borderTop:`1px solid ${BORDER}` }}>
            <p className="text-[9px] italic font-sans" style={{ color:'#5a5a5a' }}>
              <Info className="w-2.5 h-2.5 inline mr-1" />
              Neither side is presumed guilty or liable. This analysis is based solely on the uploaded document.
            </p>
          </div>
        </div>

        {/* Section 6 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={6} title="Rights & Next Steps" />
          <div className="grid grid-cols-3" style={{ borderTop:`1px solid ${BORDER}` }}>
            <div className="p-3" style={{ borderRight:`1px solid ${BORDER}`, background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8.5px] font-bold uppercase tracking-widest mb-1.5 font-sans" style={{ color: GOLD_D }}>Person's Role</p>
              <p className={`text-[10.5px] font-sans ${isBlank(report.persons_role) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.persons_role || 'Requires verification'}
              </p>
            </div>
            <div className="p-3 col-span-2" style={{ background:'rgba(8,8,8,0.9)' }}>
              <p className="text-[8.5px] font-bold uppercase tracking-widest mb-1.5 font-sans" style={{ color: GOLD_D }}>Practical Next Steps / Deadlines</p>
              <p className={`text-[10.5px] leading-relaxed font-sans whitespace-pre-line ${isBlank(report.rights_next_steps) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.rights_next_steps || 'Requires verification'}
              </p>
            </div>
          </div>
        </div>

        {/* Section 7 */}
        <div className="rounded overflow-hidden" style={{ border:`1px solid ${BORDER}` }}>
          <SecHeader n={7} title="Advocate Review / Case Status" />
          <div className="grid grid-cols-3" style={{ borderTop:`1px solid ${BORDER}` }}>
            <div className="p-3" style={{ borderRight:`1px solid ${BORDER}`, background:'rgba(8,8,8,0.9)' }}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <BookOpen className="w-3 h-3" style={{ color: GOLD }} />
                <p className="text-[8.5px] font-bold uppercase tracking-widest font-sans" style={{ color: GOLD }}>Questions for Advocate</p>
              </div>
              <p className={`text-[10.5px] leading-relaxed font-sans whitespace-pre-line ${isBlank(report.advocate_questions) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.advocate_questions || 'Requires verification'}
              </p>
            </div>
            <div className="p-3" style={{ borderRight:`1px solid ${BORDER}`, background:'rgba(8,8,8,0.9)' }}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Scale className="w-3 h-3" style={{ color: GOLD }} />
                <p className="text-[8.5px] font-bold uppercase tracking-widest font-sans" style={{ color: GOLD }}>Current Stage & Next Action</p>
              </div>
              <p className={`text-[10.5px] font-sans ${isBlank(report.current_stage) ? 'italic text-[#4a4a4a]' : 'text-[#EDEDED]'}`}>
                {report.current_stage || 'Requires verification'}
              </p>
            </div>
            <div className="p-3" style={{ background:'rgba(8,8,8,0.9)' }}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Clock className="w-3 h-3 text-[#8A8A8A]" />
                <p className="text-[8.5px] font-bold uppercase tracking-widest font-sans text-[#8A8A8A]">Last Updated</p>
              </div>
              <p className="text-[10.5px] font-sans text-[#EDEDED]">
                Date: {report.last_updated_date || 'Requires verification'}
              </p>
              <p className="text-[10.5px] font-sans text-[#EDEDED] mt-0.5">Version: {report.version}</p>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="rounded p-3" style={{ background:'rgba(168,80,20,0.07)', border:`1px solid rgba(217,164,65,0.18)` }}>
          <p className="text-[10px] leading-relaxed font-sans" style={{ color:'#b87030' }}>
            <strong className="text-[#D9A441]">IMPORTANT:</strong> AI-assisted information only; not a police finding, court decision or
            substitute for a qualified advocate. Allegations are not proven facts. Legal provisions and deadlines must be verified
            against authoritative, current sources and the incident date. If information is missing or uncertain, it is displayed as
            "Not provided" or "Requires verification" — details are never invented.
          </p>
        </div>
        <p className="text-[9px] italic pb-2 font-sans" style={{ color:'#3a3a3a' }}>
          CONFIDENTIAL — Contains personal and potentially sensitive case information. Share only with authorised people.
        </p>
      </div>
    </motion.div>
  );
}
