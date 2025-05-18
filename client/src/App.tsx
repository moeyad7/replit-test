import React from 'react';
import { ChatContainer } from './components/chat/ChatContainer';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto h-screen">
        <ChatContainer />
      </div>
    </div>
  );
}

export default App;
