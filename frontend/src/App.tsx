import { useState, useCallback } from 'react';
import Layout from './components/Layout';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import { useWebSocket } from './hooks/useWebSocket';

// Define a type for the message object for better type safety
export interface Message {
  id: number;
  sender: 'user' | 'bot';
  text: string;
}

// This is the initial dummy data, which will be managed by state now
const initialMessages: Message[] = [
  { id: 1, sender: 'user', text: 'Hello, I have a question about my recent order.' },
  { id: 2, sender: 'bot', text: 'Of course! I can help with that. What is your order number?' },
  { id: 3, sender: 'user', text: 'My order number is #12345.' },
];


function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');

  const addMessage = useCallback((newMessage: Omit<Message, 'id'>) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: prevMessages.length + 1, ...newMessage },
    ]);
  }, []);

  const { isConnected, sendMessage } = useWebSocket(addMessage);

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;

    const userMessage: Message = {
      id: messages.length + 1,
      sender: 'user',
      text: inputValue,
    };

    setMessages([...messages, userMessage]);
    sendMessage(inputValue); // Send message through WebSocket
    setInputValue('');
  };

  return (
    <Layout>
      <ChatHistory messages={messages} />
      <MessageInput
        inputValue={inputValue}
        setInputValue={setInputValue}
        onSendMessage={handleSendMessage}
        isConnected={isConnected}
      />
    </Layout>
  );
}

export default App;
