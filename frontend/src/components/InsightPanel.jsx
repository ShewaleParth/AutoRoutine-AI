import { useState, useEffect } from 'react';
import { Lightbulb, AlertTriangle, CalendarDays, Zap, RefreshCw } from 'lucide-react';
import { getInsights, runWorkflow } from '../api/client';

export default function InsightPanel({ userId = 'demo_user', onInsightTrigger }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [briefing, setBriefing] = useState(null);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const res = await getInsights(userId);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

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

  useEffect(() => {
    fetchInsights();
  }, [userId]);

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
          <button className="btn-primary" onClick={executeBriefing} disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Synthesizing...' : 'Run Analysis'}
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
