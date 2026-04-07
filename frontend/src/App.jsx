import { useState } from 'react';
import Chat from './components/Chat';
import TaskList from './components/TaskList';
import InsightPanel from './components/InsightPanel';

export default function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Called when insights/workflows modify DB to refresh TaskList
  const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

  return (
    <div className="app-container">
      {/* Left Sidebar - Insights */}
      <div>
        <InsightPanel onInsightTrigger={triggerRefresh} />
      </div>

      {/* Center - Main Chat Agent */}
      <div>
        <Chat />
      </div>

      {/* Right Sidebar - Output State (Tasks) */}
      <div>
        <TaskList refreshTrigger={refreshTrigger} />
      </div>
    </div>
  );
}
