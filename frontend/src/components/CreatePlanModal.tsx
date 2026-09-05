import { useState, useEffect } from 'react';
import { X, Calendar, CheckCircle2, Loader2 } from 'lucide-react';
import type { Platform } from '../types';
import { projectApi, planApi } from '../services/api';
import { useToast } from '../hooks/useToast';

interface CreatePlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPlanCreated: (planId: number) => void;
}

const DEFAULT_START = new Date();
DEFAULT_START.setDate(1);
const DEFAULT_END = new Date(DEFAULT_START);
DEFAULT_END.setMonth(DEFAULT_END.getMonth() + 1);
DEFAULT_END.setDate(0);

export function CreatePlanModal({ isOpen, onClose, onPlanCreated }: CreatePlanModalProps) {
  const { showToast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [projects, setProjects] = useState<{ id: number; name: string }[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [startDate, setStartDate] = useState(formatDate(DEFAULT_START));
  const [endDate, setEndDate] = useState(formatDate(DEFAULT_END));
  const [platforms, setPlatforms] = useState<Platform[]>(['instagram', 'linkedin']);
  const [objective, setObjective] = useState('');
  const [additionalInstructions, setAdditionalInstructions] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadProjects();
    }
  }, [isOpen]);

  const loadProjects = async () => {
    try {
      const response = await projectApi.list();
      setProjects(response.data);
      if (response.data.length > 0 && !selectedProject) {
        setSelectedProject(response.data[0].id);
      }
    } catch (error) {
      showToast('Failed to load projects', 'error');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) return;
    
    setIsSubmitting(true);
    try {
      const response = await planApi.create(selectedProject, {
        start_date: startDate,
        end_date: endDate,
        platforms,
        objective: objective || undefined,
        additional_instructions: additionalInstructions || undefined,
      });
      showToast('Monthly plan created!', 'success');
      onPlanCreated(response.data.plan_id);
      onClose();
    } catch (error: any) {
      showToast(error.response?.data?.message || 'Failed to create plan', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePlatform = (platform: Platform) => {
    setPlatforms(prev => prev.includes(platform) 
      ? prev.filter(p => p !== platform) 
      : [...prev, platform]
    );
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create Monthly Plan</h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={20} /></button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label className="label">Project</label>
            <select 
              className="input" 
              value={selectedProject || ''} 
              onChange={(e) => setSelectedProject(Number(e.target.value))}
              required
            >
              <option value="">Select project</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="label">Start Date <Calendar size={14} /></label>
              <input
                type="date"
                className="input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="label">End Date <Calendar size={14} /></label>
              <input
                type="date"
                className="input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="label">Platforms</label>
            <div className="platform-checkboxes">
              {(['instagram', 'linkedin'] as Platform[]).map(platform => (
                <label key={platform} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={platforms.includes(platform)}
                    onChange={() => togglePlatform(platform)}
                  />
                  <span className="platform-name" style={{ color: platform === 'instagram' ? '#E4405F' : '#0A66C2' }}>
                    {platform.charAt(0).toUpperCase() + platform.slice(1)}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="label">Marketing Objective (Optional)</label>
            <textarea
              className="input"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={3}
              placeholder="e.g., Increase product awareness and audience engagement for Q4"
            />
          </div>

          <div className="form-group">
            <label className="label">Additional Instructions (Optional)</label>
            <textarea
              className="input"
              value={additionalInstructions}
              onChange={(e) => setAdditionalInstructions(e.target.value)}
              rows={2}
              placeholder="Any specific guidance for the AI strategist..."
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting || !selectedProject}>
              {isSubmitting ? (
                <>
                  <Loader2 className="spin" size={16} /> Creating Plan...
                </>) : (
                  <>
                    <CheckCircle2 size={16} /> Create Plan
                  </>
                )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}