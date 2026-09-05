import { useState, useMemo, useEffect } from 'react';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { ChevronLeft, ChevronRight, Plus, Loader2 } from 'lucide-react';
import type { CalendarResponse, CalendarEntryResponse, EntryStatus, Platform } from '../types';

interface CalendarProps {
  calendarData: CalendarResponse | null;
  onDateClick: (date: Date, entries: CalendarEntryResponse[]) => void;
  onCreatePlan: () => void;
  isLoading: boolean;
}

const PLATFORM_COLORS: Record<Platform, string> = {
  instagram: '#E4405F',
  linkedin: '#0A66C2',
};

export function Calendar({ 
  calendarData, 
  onDateClick, 
  onCreatePlan, 
  isLoading
}: CalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  // Robust date parsing without UTC offset shifts
  const parseLocalDate = (dateStr: string): Date => {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day || 1);
  };

  // Set initial month when calendar data first loads
  useEffect(() => {
    if (calendarData && calendarData.start_date) {
      const planStart = parseLocalDate(calendarData.start_date);
      setCurrentMonth(planStart);
    }
  }, [calendarData?.start_date]);

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const entriesByDate = useMemo(() => {
    if (!calendarData) return {};
    const map: Record<string, CalendarEntryResponse[]> = {};
    calendarData.entries.forEach(entry => {
      const key = entry.date;
      if (!map[key]) map[key] = [];
      map[key].push(entry);
    });
    return map;
  }, [calendarData]);

  const getEntriesForDay = (date: Date) => {
    const key = format(date, 'yyyy-MM-dd');
    return entriesByDate[key] || [];
  };

  const isCurrentMonth = (date: Date) => isSameMonth(date, currentMonth);
  const isToday = (date: Date) => isSameDay(date, new Date());

  const goToPrevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const goToNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));

  const getStatusBadge = (status: EntryStatus) => (
    <span className={`badge badge-${status}`}>{status}</span>
  );

  // Generation status metrics across unified timeline
  const totalEntries = calendarData?.entries.length || 0;
  const readyEntries = calendarData?.entries.filter(e => e.status === 'ready' || e.status === 'skipped').length || 0;
  const activeGeneratingCount = calendarData?.entries.filter(
    e => e.status === 'generating' || e.status === 'queued' || e.status === 'regenerating' || e.status === 'retrying'
  ).length || 0;
  const isGenerating = activeGeneratingCount > 0 || (totalEntries === 0 && isLoading);
  const progressPercent = totalEntries > 0 ? Math.round((readyEntries / totalEntries) * 100) : 0;

  const renderDayCell = (date: Date) => {
    const entries = getEntriesForDay(date);
    const isEmpty = entries.length === 0;
    const inCurrentMonth = isCurrentMonth(date);

    return (
      <div
        key={format(date, 'yyyy-MM-dd')}
        className={`calendar-day ${!inCurrentMonth ? 'other-month' : ''} ${isToday(date) ? 'today' : ''} ${isEmpty ? 'empty' : 'has-entries'}`}
        onClick={() => {
          if (!isEmpty) {
            onDateClick(date, entries);
          }
        }}
        style={{ cursor: isEmpty ? 'default' : 'pointer' }}
      >
        <div className="day-number">{format(date, 'd')}</div>
        
        {!isEmpty && (
          <div className="day-entries">
            {entries.map((entry, index) => (
              <div key={`${entry.id}-${entry.platform}-${index}`} className="day-entry" onClick={(e) => { e.stopPropagation(); onDateClick(date, [entry]); }}>
                <span className="entry-type-badge" style={{ backgroundColor: PLATFORM_COLORS[entry.platform], color: 'white' }}>
                  {entry.content_type?.toUpperCase() || 'POST'}
                </span>
                <span className="entry-title" title={entry.title}>{entry.title}</span>
                <span className="entry-status">{getStatusBadge(entry.status)}</span>
              </div>
            ))}
          </div>
        )}

        {isEmpty && inCurrentMonth && (
          <div className="empty-day-indicator" title="No post recommended">
            <span className="empty-text">No post</span>
          </div>
        )}
      </div>
    );
  };

  if (isLoading && !calendarData) {
    return (
      <div className="calendar-loading card">
        <Loader2 className="spin" size={32} />
        <p>Loading unified marketing calendar...</p>
      </div>
    );
  }

  return (
    <div className="calendar-container card">
      {/* Live Generation Progress Banner */}
      {isGenerating && (
        <div className="plan-generation-banner">
          <div className="banner-content">
            <Loader2 className="spin" size={18} />
            <span>AI generating content recommendations... ({readyEntries} of {totalEntries || '?'} ready)</span>
          </div>
          {totalEntries > 0 && (
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          )}
        </div>
      )}

      <div className="calendar-header">
        <div className="calendar-title-section">
          <button className="btn btn-ghost" onClick={goToPrevMonth} aria-label="Previous month">
            <ChevronLeft size={20} />
          </button>
          <h2 className="calendar-month-title">{format(currentMonth, 'MMMM yyyy')}</h2>
          <button className="btn btn-ghost" onClick={goToNextMonth} aria-label="Next month">
            <ChevronRight size={20} />
          </button>
        </div>
        
        <div className="calendar-header-actions">
          <button className="btn btn-primary" onClick={onCreatePlan}>
            <Plus size={18} /> Create Monthly Plan
          </button>
        </div>
      </div>

      <div className="calendar-weekdays">
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
          <div key={day} className="weekday">{day}</div>
        ))}
      </div>

      <div className="calendar-grid" role="grid">
        {days.map(renderDayCell)}
      </div>

      {calendarData && (
        <div className="calendar-summary">
          <div className="summary-stats">
            <span><strong>{calendarData.planned_posts}</strong> total posts scheduled</span>
            <span><strong>{calendarData.empty_days}</strong> empty days</span>
            <span><strong>{calendarData.total_days}</strong> timeline days</span>
          </div>
          {calendarData.strategy_summary && (
            <div className="strategy-summary">
              <strong>Strategy:</strong> {calendarData.strategy_summary}
            </div>
          )}
        </div>
      )}
    </div>
  );
}