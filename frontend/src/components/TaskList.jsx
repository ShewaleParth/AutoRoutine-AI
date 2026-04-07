import { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Flag, Clock, RefreshCw, Layers } from 'lucide-react';
import { getTasks } from '../api/client';

export default function TaskList({ userId = 'demo_user', refreshTrigger }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const { data } = await getTasks(userId);
      const sorted = data.sort((a, b) => {
        if (a.status !== b.status) return a.status === 'pending' ? -1 : 1;
        return (b.priority || 3) - (a.priority || 3);
      });
      setTasks(sorted);
    } catch (e) {
      console.error("Failed to load tasks", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [userId, refreshTrigger]);

  const priorityColor = (p) => {
    if (p >= 5) return 'var(--accent-secondary)'; // critical (pink/rose)
    if (p === 4) return '#f59e0b'; // high (amber)
    if (p === 3) return 'var(--accent-primary)'; // normal (indigo)
    return 'var(--text-subtle)'; // low
  };

  return (
    <div className="glass-panel">
      <div className="panel-header">
        <h2 className="panel-title">
          <div className="panel-icon-wrapper">
            <Layers size={20} color="var(--accent-secondary)" strokeWidth={2.5} />
          </div>
          Action Items
        </h2>
        <button className="btn-icon-subtle" onClick={fetchTasks}>
          <RefreshCw size={18} className={loading ? 'animate-spin-slow' : ''} />
        </button>
      </div>

      <div className="panel-content">
        {loading && tasks.length === 0 ? (
          <div className="text-sm" style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px' }}>
            Syncing tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-sm" style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px' }}>
            Inbox Zero. You're all caught up!
          </div>
        ) : (
          tasks.map(task => {
            const isDone = task.status === 'done';
            return (
              <div 
                key={task.id || task.task_id || Math.random()} 
                className="premium-card"
                style={{ 
                  '--card-color': isDone ? 'transparent' : priorityColor(task.priority),
                  opacity: isDone ? 0.6 : 1,
                  filter: isDone ? 'grayscale(100%)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                  <div style={{ marginTop: '3px', color: isDone ? 'var(--text-subtle)' : 'var(--text-muted)' }}>
                    {isDone ? <CheckCircle2 size={20} /> : <Circle size={20} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <h4 className="text-lg" style={{ margin: '0 0 10px 0', textDecoration: isDone ? 'line-through' : 'none' }}>
                      {task.title}
                    </h4>
                    
                    <div className="flex-row" style={{ flexWrap: 'wrap', gap: '12px' }}>
                      <span className="status-tag" style={{ background: `color-mix(in srgb, ${priorityColor(task.priority)} 15%, transparent)`, color: priorityColor(task.priority) }}>
                        <Flag size={12} strokeWidth={3} />
                        Pri {task.priority || 3}
                      </span>
                      
                      {task.due_date && (
                        <span className="text-xs flex-row">
                          <Clock size={14} /> 
                          {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
