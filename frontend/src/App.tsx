import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { Sun, Moon, RefreshCw, Plus } from 'lucide-react';
import { Calendar } from './components/Calendar';
import { RecommendationDetail } from './components/RecommendationDetail';
import { CreatePlanModal } from './components/CreatePlanModal';
import { ToastProvider, useToast } from './hooks/useToast';
import { planApi } from './services/api';
import type { CalendarResponse, CalendarEntryResponse, DayRecommendationResponse } from './types';

function AppContent() {
  const { showToast } = useToast();
  const [calendarData, setCalendarData] = useState<CalendarResponse | null>(null);
  const [selectedRecommendations, setSelectedRecommendations] = useState<DayRecommendationResponse[] | null>(null);
  const [isCalendarLoading, setIsCalendarLoading] = useState(false);
  const [showCreatePlanModal, setShowCreatePlanModal] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const loadUnifiedCalendar = useCallback(async (showErrorToast = true) => {
    setIsCalendarLoading(true);
    try {
      const res = await planApi.getUnifiedCalendar();
      setCalendarData(res.data);
    } catch (error) {
      if (showErrorToast) {
        showToast('Failed to load unified calendar', 'error');
      }
    } finally {
      setIsCalendarLoading(false);
    }
  }, [showToast]);

  const handleDateClick = useCallback(async (date: Date, entries: CalendarEntryResponse[]) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    try {
      const res = await planApi.getEntriesByDate(dateStr);
      setSelectedRecommendations(res.data);
    } catch (error) {
      const fallbackRecs: DayRecommendationResponse[] = entries.map(e => ({
        id: e.id,
        plan_id: e.plan_id,
        date: e.date,
        platform: e.platform,
        content_type: e.content_type,
        title: e.title,
        objective: e.objective,
        audience: e.audience,
        product: e.product,
        content_pillar: e.content_pillar,
        reason: e.reason,
        hook: e.hook,
        concept: e.concept,
        caption_direction: e.caption_direction,
        cta: e.cta,
        visual_direction: e.visual_direction,
        image_prompt: e.image_prompt,
        review_status: e.review_status,
        review_score: e.review_score,
        review_issues: e.review_issues,
        review_corrections: e.review_corrections,
        image_status: e.image_status,
        image_url: e.image_url,
        image_prompt_used: e.image_prompt_used,
        status: e.status,
        error: e.error,
        is_empty: false
      }));
      setSelectedRecommendations(fallbackRecs);
    }
  }, []);

  const handlePlanCreated = async () => {
    await loadUnifiedCalendar(true);
  };

  const handleCloseRecommendation = () => {
    setSelectedRecommendations(null);
  };

  // Initial load once on mount
  useEffect(() => {
    loadUnifiedCalendar(true);
  }, []);

  // Auto-polling for active background generation
  useEffect(() => {
    if (!calendarData || !calendarData.entries) return;

    const hasActiveGeneration = calendarData.entries.some(
      e => e.status === 'queued' || e.status === 'generating' || e.status === 'retrying' || e.status === 'regenerating'
    );

    if (!hasActiveGeneration) return;

    const interval = setInterval(() => {
      loadUnifiedCalendar(false);
    }, 3000);

    return () => clearInterval(interval);
  }, [calendarData, loadUnifiedCalendar]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => setDarkMode(e.matches);
    setDarkMode(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <div className={`app ${darkMode ? 'dark' : ''}`}>
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">📅</span>
            <span className="logo-text">Qicdock Marketing Calendar</span>
          </div>
        </div>
        <div className="header-right">
          <button className="btn btn-primary" onClick={() => setShowCreatePlanModal(true)}>
            <Plus size={18} /> Create Monthly Plan
          </button>
          <button className="btn btn-ghost" onClick={loadUnifiedCalendar} disabled={isCalendarLoading} title="Refresh Calendar">
            <RefreshCw size={18} className={isCalendarLoading ? 'spin' : ''} />
          </button>
          <button className="btn btn-ghost" onClick={() => setDarkMode(!darkMode)} title="Toggle theme">
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      <main className="app-main container">
        <Calendar
          calendarData={calendarData}
          onDateClick={handleDateClick}
          onCreatePlan={() => setShowCreatePlanModal(true)}
          isLoading={isCalendarLoading}
        />

        {selectedRecommendations && (
          <RecommendationDetail
            recommendations={selectedRecommendations}
            onClose={handleCloseRecommendation}
            onRefresh={loadUnifiedCalendar}
          />
        )}

        <CreatePlanModal
          isOpen={showCreatePlanModal}
          onClose={() => setShowCreatePlanModal(false)}
          onPlanCreated={handlePlanCreated}
        />
      </main>
    </div>
  );
}

function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}

export default App;