import { useState, useEffect } from 'react';
import { X, Image, Loader2, RefreshCw, CheckCircle, AlertCircle, Copy, Download, Layers, FileText } from 'lucide-react';
import jsPDF from 'jspdf';
import type { DayRecommendationResponse, EntryStatus, ImageStatus, ReviewStatus, Platform } from '../types';
import { planApi } from '../services/api';
import { useToast } from '../hooks/useToast';

interface RecommendationDetailProps {
  recommendation?: DayRecommendationResponse | null;
  recommendations?: DayRecommendationResponse[] | null;
  planId?: number;
  onClose: () => void;
  onRefresh: () => void;
}

const STATUS_LABELS: Record<EntryStatus, string> = {
  planned: 'Planned',
  queued: 'Queued',
  generating: 'Generating...',
  ready: 'Ready',
  failed: 'Failed',
  retrying: 'Retrying',
  skipped: 'Skipped',
  regenerating: 'Regenerating...',
};

const IMAGE_STATUS_LABELS: Record<ImageStatus, string> = {
  not_requested: 'Not Generated',
  queued: 'Queued',
  generating: 'Generating...',
  ready: 'Generated',
  failed: 'Failed',
};

const REVIEW_STATUS_LABELS: Record<ReviewStatus, string> = {
  pending: 'Pending Review',
  approved: 'Approved',
  needs_revision: 'Needs Revision',
  failed: 'Review Failed',
};

const PLATFORM_COLORS: Record<Platform, string> = {
  instagram: '#E4405F',
  linkedin: '#0A66C2',
};

const PLATFORM_LABELS: Record<Platform, string> = {
  instagram: 'Instagram',
  linkedin: 'LinkedIn',
};

export function RecommendationDetail({ recommendation, recommendations, planId, onClose, onRefresh }: RecommendationDetailProps) {
  const { showToast } = useToast();
  const [activeIndex, setActiveIndex] = useState(0);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isRegeneratingPrompt, setIsRegeneratingPrompt] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeSlide, setActiveSlide] = useState(0);

  // Normalize single or multiple recommendations prop
  const list: DayRecommendationResponse[] = recommendations && recommendations.length > 0
    ? recommendations
    : recommendation
      ? [recommendation]
      : [];

  const currentRec = list[activeIndex] || null;

  useEffect(() => {
    setActiveIndex(0);
  }, [recommendations, recommendation]);

  useEffect(() => {
    if (currentRec && (currentRec.status === 'ready' || currentRec.status === 'failed')) {
      const interval = setInterval(() => {
        onRefresh();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [currentRec, onRefresh]);

  const handleRegenerate = async () => {
    if (!currentRec || isRegenerating) return;
    setIsRegenerating(true);
    try {
      if (currentRec.id) {
        await planApi.regenerateById(currentRec.id, { feedback: feedback || undefined });
      } else if (planId) {
        await planApi.regenerate(planId, currentRec.date, { feedback: feedback || undefined }, currentRec.platform);
      }
      showToast('Regeneration started', 'success');
      setShowFeedbackInput(false);
      setFeedback('');
      onRefresh();
    } catch (error) {
      showToast('Failed to start regeneration', 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!currentRec || isGeneratingImage) return;
    setIsGeneratingImage(true);
    try {
      if (currentRec.id) {
        await planApi.generateImageById(currentRec.id, { prompt: currentRec.image_prompt });
      } else if (planId) {
        await planApi.generateImage(planId, currentRec.date, { prompt: currentRec.image_prompt }, currentRec.platform);
      }
      showToast('Image generation started', 'success');
      onRefresh();
    } catch (error) {
      showToast('Failed to start image generation', 'error');
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const copyToClipboard = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleDownloadPDF = () => {
    if (!currentRec) return;
    
    const doc = new jsPDF();
    const margin = 20;
    let y = margin;
    const lineHeight = 7;
    const pageHeight = doc.internal.pageSize.height;
    
    // Helper to sanitize text for jsPDF (removes emojis and weird unicode that break standard fonts)
    const sanitize = (text: string) => {
      if (!text) return 'N/A';
      return text.replace(/[^\x00-\x7F]/g, "").replace(/\s+/g, ' ').trim();
    };
    
    const addText = (text: string, fontSize = 12, isBold = false) => {
      doc.setFontSize(fontSize);
      doc.setFont('helvetica', isBold ? 'bold' : 'normal');
      
      const cleanText = sanitize(text);
      const splitText = doc.splitTextToSize(cleanText, 170);
      
      for (let i = 0; i < splitText.length; i++) {
        if (y > pageHeight - margin) {
          doc.addPage();
          y = margin;
        }
        doc.text(splitText[i], margin, y);
        y += lineHeight;
      }
      y += 4; // Add some paragraph spacing
    };

    // Header
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text(`Qicdock Recommendation: ${format(currentRec.date, 'MMMM d, yyyy')}`, margin, y);
    y += 15;

    addText('Title: ' + (currentRec.title || ''), 14, true);
    addText(`Platform: ${PLATFORM_LABELS[currentRec.platform]} | Type: ${currentRec.content_type?.replace('_', ' ')}`);
    y += 5;

    addText('Strategy', 14, true);
    addText(currentRec.reason || '');

    addText('Hook', 14, true);
    addText(currentRec.hook || '');

    addText('Angle', 14, true);
    addText(currentRec.concept || '');

    addText('Content Structure', 14, true);
    addText(currentRec.caption_direction || '');

    addText('Caption', 14, true);
    addText(currentRec.visual_direction || '');

    addText('Call to Action (CTA)', 14, true);
    addText(currentRec.cta || '');
    
    addText('Creative Prompt', 14, true);
    const promptText = (currentRec.image_prompts && currentRec.image_prompts.length > 0) 
      ? currentRec.image_prompts.map((p, i) => `Slide ${i+1}: ${p}`).join('\n\n')
      : currentRec.image_prompt || '';
    addText(promptText);

    doc.save(`Qicdock_Recommendation_${currentRec.date}.pdf`);
  };

  const handleDownloadImage = async (url: string, slideIndex: number) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `Qicdock_Generated_Image_${currentRec?.date}_Slide${slideIndex + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Failed to download image', error);
      showToast('Failed to download image', 'error');
    }
  };

  if (!currentRec) return null;

  if (currentRec.is_empty) {
    return (
      <div className="sidebar-panel">
        <div className="panel-header">
          <h2>{format(currentRec.date, 'MMMM d, yyyy')}</h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="panel-content">
          <div className="empty-recommendation">
            <div className="empty-icon">📅</div>
            <h3>No Post Recommended</h3>
            <p>{currentRec.empty_reason || 'The marketing strategist determined this day should remain empty to maintain optimal content cadence.'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (currentRec.status === 'generating' || currentRec.status === 'queued' || currentRec.status === 'regenerating') {
    return (
      <div className="sidebar-panel">
        <div className="panel-header">
          <h2>{format(currentRec.date, 'MMMM d, yyyy')}</h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={20} /></button>
        </div>
        <div className="panel-content generating">
          <Loader2 className="spin" size={32} />
          <h3>{STATUS_LABELS[currentRec.status]} Recommendation</h3>
          <p>Please wait while the AI marketing strategist prepares your content...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar-panel">
      <div className="panel-header">
        <div>
          <span className="platform-badge" style={{ backgroundColor: PLATFORM_COLORS[currentRec.platform] }}>
            {PLATFORM_LABELS[currentRec.platform]}
          </span>
          <span className="date-text">{format(currentRec.date, 'MMMM d, yyyy')}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-ghost" onClick={handleDownloadPDF} title="Download PDF Report">
            <FileText size={18} />
          </button>
          <button className="btn btn-ghost" onClick={onClose}><X size={20} /></button>
        </div>
      </div>

      {/* Multi-entry Tabs */}
      {list.length > 1 && (
        <div className="entry-tabs" style={{ display: 'flex', gap: '8px', padding: '12px 24px', background: '#f5f5f5', borderBottom: '1px solid #cccccc' }}>
          {list.map((item, idx) => (
            <button
              key={item.id || idx}
              className={`btn btn-sm ${idx === activeIndex ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveIndex(idx)}
              style={{ fontSize: '12px' }}
            >
              <Layers size={14} /> {PLATFORM_LABELS[item.platform]} {item.content_type ? `(${item.content_type.replace('_', ' ')})` : ''}
            </button>
          ))}
        </div>
      )}

      <div className="panel-content scrollbar-thin">
        <div className="recommendation-header">
          <div className="status-row">
            <span className={`badge badge-${currentRec.status}`}>{STATUS_LABELS[currentRec.status]}</span>
            <span className={`badge badge-${currentRec.review_status}`}>{REVIEW_STATUS_LABELS[currentRec.review_status]}</span>
            {currentRec.image_status !== 'not_requested' && (
              <span className={`badge badge-${currentRec.image_status}`}>
                <Image size={12} /> {IMAGE_STATUS_LABELS[currentRec.image_status]}
              </span>
            )}
          </div>
          <h3 className="recommendation-title">{currentRec.title}</h3>
          <div className="meta-row">
            <span><strong>Type:</strong> {currentRec.content_type?.replace('_', ' ')}</span>
            <span><strong>Objective:</strong> {currentRec.objective}</span>
            <span><strong>Pillar:</strong> {currentRec.content_pillar}</span>
            {currentRec.product && <span><strong>Product:</strong> {currentRec.product}</span>}
            {currentRec.audience && <span><strong>Audience:</strong> {currentRec.audience}</span>}
          </div>
        </div>

        <div className="section">
          <h4>Strategy</h4>
          <p className="reason-text" style={{ whiteSpace: 'pre-line' }}>{currentRec.reason}</p>
        </div>

        <div className="section">
          <h4>Hook</h4>
          <div className="copyable-field">
            <p>{currentRec.hook}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentRec.hook || '', 'hook')}>
              {copiedField === 'hook' ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div className="section">
          <h4>Angle</h4>
          <div className="copyable-field">
            <p>{currentRec.concept}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentRec.concept || '', 'concept')}>
              {copiedField === 'concept' ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div className="section">
          <h4>Content Structure</h4>
          <div className="copyable-field">
            <p style={{ whiteSpace: 'pre-line' }}>{currentRec.caption_direction}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentRec.caption_direction || '', 'content_structure')}>
              {copiedField === 'content_structure' ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div className="section">
          <h4>CTA</h4>
          <div className="copyable-field">
            <p>{currentRec.cta}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentRec.cta || '', 'cta')}>
              {copiedField === 'cta' ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div className="section">
          <h4>Caption</h4>
          <div className="copyable-field">
            <p style={{ whiteSpace: 'pre-line' }}>{currentRec.visual_direction}</p>
            <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentRec.visual_direction || '', 'visual_direction')}>
              {copiedField === 'visual_direction' ? <CheckCircle size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div className="section image-prompt-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4>Creative Prompt</h4>
            <button 
              className="btn btn-secondary btn-sm" 
              onClick={async () => {
                try {
                  setIsRegeneratingPrompt(true);
                  const res = await planApi.regenerateImagePrompt(currentRec.id!);
                  // Force refresh from parent to get new data
                  onRefresh();
                } catch (e) {
                  console.error(e);
                  alert("Failed to regenerate prompt");
                } finally {
                  setIsRegeneratingPrompt(false);
                }
              }}
              disabled={isRegeneratingPrompt}
            >
              {isRegeneratingPrompt ? (
                <><span className="loading loading-spinner loading-xs"></span> Regenerating...</>
              ) : (
                <><RefreshCw size={12} className="mr-1" /> Regenerate Prompt</>
              )}
            </button>
          </div>
          <div className="section-label">Generated Images & Prompts</div>
          
          {/* Determine how many slides we have based on prompts or urls */}
          {(() => {
            const hasMultiplePrompts = currentRec.image_prompts && currentRec.image_prompts.length > 1;
            const hasMultipleUrls = currentRec.image_urls && currentRec.image_urls.length > 1;
            const isMultiSlide = hasMultiplePrompts || hasMultipleUrls;
            const slideCount = hasMultipleUrls 
              ? currentRec.image_urls!.length 
              : (hasMultiplePrompts ? currentRec.image_prompts!.length : 1);
            
            const currentPrompt = (currentRec.image_prompts && currentRec.image_prompts.length > activeSlide)
              ? currentRec.image_prompts[activeSlide]
              : currentRec.image_prompt;
              
            const currentUrl = (currentRec.image_urls && currentRec.image_urls.length > activeSlide)
              ? currentRec.image_urls[activeSlide]
              : currentRec.image_url;

            return (
              <div style={{ marginTop: '16px' }}>
                {isMultiSlide && (
                  <div className="carousel-controls" style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                    {Array.from({ length: slideCount }).map((_, i) => (
                      <button
                        key={i}
                        className={`btn btn-sm ${i === activeSlide ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveSlide(i)}
                      >
                        Slide {i + 1}
                      </button>
                    ))}
                  </div>
                )}
                
                <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px', background: '#f9f9f9' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '14px', color: '#000' }}>
                    {isMultiSlide ? `Slide ${activeSlide + 1} Prompt` : 'Creative Prompt'}
                  </div>
                  
                  <div className="copyable-field" style={{ background: '#fff', border: '1px solid #eee', padding: '12px', borderRadius: '4px' }}>
                    <p style={{ color: '#000', margin: 0 }}>{currentPrompt}</p>
                    <button className="btn btn-ghost btn-sm" onClick={() => copyToClipboard(currentPrompt || '', `image_prompt_${activeSlide}`)}>
                      {copiedField === `image_prompt_${activeSlide}` ? <CheckCircle size={14} /> : <Copy size={14} />}
                    </button>
                  </div>

                  {currentUrl && (
                    <div className="generated-image" style={{ position: 'relative', marginTop: '16px' }}>
                      <img src={currentUrl} alt={`Generated slide ${activeSlide + 1}`} style={{ width: '100%', borderRadius: '8px', border: '1px solid #ccc' }} />
                      <button 
                        className="btn btn-sm" 
                        style={{ position: 'absolute', bottom: '8px', right: '8px', background: 'rgba(255,255,255,0.9)', color: '#000', border: '1px solid #ccc' }}
                        onClick={() => handleDownloadImage(currentUrl, activeSlide)}
                      >
                        <Download size={14} /> Download
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          <button 
            className={`btn ${currentRec.image_status === 'ready' ? 'btn-secondary' : 'btn-primary'} btn-full`}
            onClick={handleGenerateImage}
            disabled={isGeneratingImage || currentRec.image_status === 'generating'}
          >
            {isGeneratingImage || currentRec.image_status === 'generating' ? (
              <>
                <Loader2 className="spin" size={16} /> Generating...
              </>
            ) : currentRec.image_status === 'ready' ? (
              <>
                <Download size={16} /> Regenerate Image
              </>
            ) : (
              <>
                <Image size={16} /> Generate Image
              </>
            )}
          </button>
        </div>

        {currentRec.review_issues && currentRec.review_issues.length > 0 && (
          <div className="section review-issues">
            <h4>Review Issues</h4>
            <ul>
              {currentRec.review_issues.map((issue, i) => (
                <li key={i}>{issue}</li>
              ))}
            </ul>
          </div>
        )}

        {currentRec.review_corrections && currentRec.review_corrections.length > 0 && (
          <div className="section review-corrections">
            <h4>Suggested Corrections</h4>
            <ul>
              {currentRec.review_corrections.map((correction, i) => (
                <li key={i}>{correction}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="action-buttons">
          <button 
            className="btn btn-secondary btn-full"
            onClick={() => setShowFeedbackInput(!showFeedbackInput)}
          >
            <RefreshCw size={16} /> {showFeedbackInput ? 'Cancel' : 'Regenerate Recommendation'}
          </button>

          {showFeedbackInput && (
            <div className="feedback-form">
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Why do you want to regenerate? (e.g., 'Make it more engaging', 'Try a carousel instead', 'Less promotional')"
                rows={3}
                className="input"
              />
              <button 
                className="btn btn-primary btn-full"
                onClick={handleRegenerate}
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <>
                    <Loader2 className="spin" size={16} /> Regenerating...
                  </>
                ) : (
                  <>
                    <RefreshCw size={16} /> Confirm Regenerate
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {currentRec.error && (
          <div className="error-message">
            <AlertCircle size={16} /> {currentRec.error}
          </div>
        )}
      </div>
    </div>
  );
}

function format(dateStr: string, fmt: string) {
  const date = new Date(dateStr);
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  
  return fmt
    .replace('MMMM', months[date.getMonth()])
    .replace('d', String(date.getDate()))
    .replace('yyyy', String(date.getFullYear()));
}