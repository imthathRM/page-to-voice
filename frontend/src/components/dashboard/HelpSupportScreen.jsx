import React, { useState } from 'react';
import './Dashboard.css';

/**
 * Help & Support Screen
 */
export function HelpSupportScreen() {
  const [openFaq, setOpenFaq] = useState(null);

  const faqs = [
    {
      q: 'Which document formats are supported?',
      a: 'Page to Voice natively supports 6 formats: PDF (.pdf), Microsoft Word (.docx), Plain Text (.txt), Microsoft PowerPoint (.pptx), Electronic Publication (.epub), and Rich Text Format (.rtf). Each parser follows a common interface with robust error handling.',
    },
    {
      q: 'Does Page to Voice support Tamil and Sinhala languages?',
      a: 'Yes! Full Unicode support is built into the document processing engine for English, Tamil (தமிழ்), and Sinhala (සිංහල). Text extraction preserves script glyphs and character boundaries accurately.',
    },
    {
      q: 'What is the maximum allowed file size?',
      a: 'The current backend upload limit is 25 MB per document. If you have larger documents, splitting them or optimizing embedded media will allow faster parsing.',
    },
    {
      q: 'How does Chapter and Section detection work?',
      a: 'Depending on the format, the parser intelligently segments your document: PDF pages/sections, DOCX headings, PPTX slides, EPUB chapters, and RTF/TXT paragraph breaks. These segments can be read or listened to individually.',
    },
    {
      q: 'What is the current status of Voice/Audiobook Generation?',
      a: 'The document processing engine, OCR evaluation, common parser factory, and database layers are fully functional. Neural Text-to-Speech (TTS) batch voice generation is being integrated by Team Member 4. The audio player bar is ready for playback with speed controls, scrubber, and chapter navigation.',
    },
  ];

  return (
    <div className="dashboard-view-container">
      {/* Overview Header */}
      <div className="dash-panel" style={{ marginBottom: '24px' }}>
        <h3 className="dash-panel-title" style={{ marginBottom: '8px' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>Page to Voice Documentation & Support</span>
        </h3>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.5 }}>
          Welcome to the help center for <strong>Page to Voice: Intelligent Audiobook Generation and Listening Platform</strong>.
          Explore the guides below or review frequently asked questions.
        </p>
      </div>

      {/* 6 Supported Formats Matrix */}
      <div className="dash-panel" style={{ marginBottom: '24px' }}>
        <h4 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)' }}>
          📄 Supported File Formats & Capabilities
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill pdf" style={{ marginBottom: '6px' }}>PDF</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Adobe Portable Document</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>PyMuPDF extraction with page boundary preservation and OCR fallback for scanned pages.</div>
          </div>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill docx" style={{ marginBottom: '6px' }}>DOCX</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Microsoft Word</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>Heading hierarchy detection, paragraph extraction, and table text capture via python-docx.</div>
          </div>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill pptx" style={{ marginBottom: '6px' }}>PPTX</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Microsoft PowerPoint</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>Slide-by-slide text extraction with slide titles and notes extracted using python-pptx.</div>
          </div>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill epub" style={{ marginBottom: '6px' }}>EPUB</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Electronic Publication</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>Chapter and spine structure extraction via EbookLib with HTML tag sanitization.</div>
          </div>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill txt" style={{ marginBottom: '6px' }}>TXT</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Plain Text</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>Robust UTF-8/Latin-1 encoding detection, Unicode preservation, and paragraph grouping.</div>
          </div>
          <div style={{ padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', background: 'var(--code-bg)' }}>
            <span className="format-pill rtf" style={{ marginBottom: '6px' }}>RTF</span>
            <div style={{ fontWeight: '600', fontSize: '13px', color: 'var(--text-h)' }}>Rich Text Format</div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>striprtf parsing removing control words while preserving Unicode symbols and layout.</div>
          </div>
        </div>
      </div>

      {/* FAQ Accordion */}
      <div className="dash-panel">
        <h4 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)' }}>
          ❓ Frequently Asked Questions
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div
                key={idx}
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  background: isOpen ? 'var(--social-bg)' : 'transparent',
                }}
              >
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  style={{
                    width: '100%',
                    padding: '14px 18px',
                    textAlign: 'left',
                    background: 'transparent',
                    border: 'none',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: varTextH,
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>{faq.q}</span>
                  <span style={{ fontSize: '16px', color: 'var(--text)' }}>
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div style={{ padding: '0 18px 16px', fontSize: '13px', color: 'var(--text)', lineHeight: 1.5 }}>
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

const varTextH = 'var(--text-h)';

export default HelpSupportScreen;
