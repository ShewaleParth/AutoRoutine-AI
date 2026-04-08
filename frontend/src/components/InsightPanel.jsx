import { useState, useEffect, useCallback } from 'react';
import { Lightbulb, AlertTriangle, CalendarDays, Zap, RefreshCw, LogIn } from 'lucide-react';
import { getInsights, runWorkflow } from '../api/client';

export default function InsightPanel({ userId = 'demo_user', onInsightTrigger }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [briefing, setBriefing] = useState(null);

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getInsights(userId);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const executeBriefing = async () => {
    setLoading(true);
    try {
      const res = await runWorkflow('morning_briefing', userId);
      setBriefing(res.data.result);
      if(onInsightTrigger) onInsightTrigger();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectCalendar = async () => {
    try {
      // Fetch the auth URL from your API
      const res = await fetch(`http://localhost:8000/api/auth/google/login?user_id=${userId}`);
      const data = await res.json();
      if (data.auth_url) {
        // Open the google login in a popup
        window.open(data.auth_url, 'Google OAuth', 'width=500,height=700');
      }
    } catch (e) {
      console.error("Failed to initiate Google Login", e);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [userId, fetchInsights]);

  return (
    <div className="glass-panel">
      <div className="panel-header">
        <h2 className="panel-title">
          <div className="panel-icon-wrapper" style={{ boxShadow: '0 0 15px rgba(16, 185, 129, 0.3)' }}>
            <Lightbulb size={20} color="var(--accent-tertiary)" strokeWidth={2.5} />
          </div>
          Intelligence
        </h2>
        <button className="btn-icon-subtle" onClick={fetchInsights}>
          <RefreshCw size={18} className={loading && !briefing ? 'animate-spin-slow' : ''} />
        </button>
      </div>

      <div className="panel-content">
        <div 
          className="premium-card" 
          style={{ 
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(244, 63, 94, 0.05))',
            '--card-color': 'var(--accent-primary)',
            borderColor: 'rgba(99, 102, 241, 0.2)'
          }}
        >
          <h3 className="text-lg flex-row" style={{ color: '#fff', marginBottom: '6px' }}>
            <Zap size={18} color="var(--accent-primary)" /> Morning Briefing
          </h3>
          <p className="text-sm" style={{ color: 'var(--text-subtle)', marginBottom: '20px', lineHeight: 1.5 }}>
            Synthesize context graph, assess blockers, and generate today's battle plan.
          </p>
          <button className="btn-primary" onClick={executeBriefing} disabled={loading} style={{ width: '100%', marginBottom: '14px' }}>
            {loading ? 'Synthesizing...' : 'Run Analysis'}
          </button>
          
          <button className="btn-google-premium" onClick={handleConnectCalendar} style={{ width: '100%' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Connect Sync
          </button>
        </div>

        {briefing && (
           <div className="premium-card" style={{ '--card-color': 'var(--accent-tertiary)' }}>
             <h4 className="text-sm" style={{ color: 'var(--accent-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
               Briefing Complete
             </h4>
             <div className="text-sm" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, color: 'var(--text-main)' }}>
               {briefing}
             </div>
           </div>
        )}

        {data?.insights?.map((inf, i) => {
          const isString = typeof inf === 'string';
          const message = isString ? inf : (inf?.message || '');
          const isWarning = message.toLowerCase().includes('warn') || message.toLowerCase().includes('conflict') || message.toLowerCase().includes('overdue');
          
          const accentTheme = isWarning ? 'var(--accent-secondary)' : 'var(--accent-primary)';
          
          return (
            <div key={i} className="premium-card" style={{ '--card-color': accentTheme }}>
              <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                <div style={{ color: accentTheme, flexShrink: 0, marginTop: '2px' }}>
                  {isWarning ? <AlertTriangle size={18} strokeWidth={2.5} /> : <CalendarDays size={18} /> }
                </div>
                <div className="text-sm" style={{ lineHeight: 1.5, color: 'var(--text-main)' }}>
                  {message}
                </div>
              </div>
            </div>
          );
        })}
        
        {!loading && !data?.insights?.length && !briefing && (
           <div className="text-sm" style={{ color: 'var(--text-subtle)', textAlign: 'center', marginTop: '20px' }}>
             No critical vectors detected. You're optimal.
           </div>
        )}
      </div>
    </div>
  );
}
