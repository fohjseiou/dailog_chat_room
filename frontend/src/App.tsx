import { ChatView } from './components/chat/ChatView';
import { SessionList } from './components/common/SessionList';

function App() {
  return (
    <div className="App flex h-screen">
      <SessionList />
      <div className="flex-1">
        <ChatView />
      </div>
    </div>
  );
}

export default App;
