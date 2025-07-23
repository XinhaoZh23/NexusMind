import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import Layout from './components/Layout';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import { useWebSocket } from './hooks/useWebSocket';
import { FileUpload } from './components/FileUpload';
import type { UploadedFile } from './components/FileUpload';

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

interface ProcessingFile extends UploadedFile {
  status: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);

  const addMessage = useCallback((newMessage: Omit<Message, 'id'>) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: prevMessages.length + 1, ...newMessage },
    ]);
  }, []);

  const { isConnected, sendMessage } = useWebSocket(addMessage);

  const handleFileUpload = (file: UploadedFile) => {
    setProcessingFiles((prevFiles) => [
      ...prevFiles,
      { ...file, status: 'PENDING' },
    ]);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      processingFiles.forEach(async (file) => {
        if (file.status === 'PENDING' || file.status === 'STARTED') {
          try {
            const response = await axios.get(`/upload-api/upload/status/${file.task_id}`);
            if (response.data.status === 'SUCCESS') {
              setProcessingFiles((prevFiles) =>
                prevFiles.map((f) =>
                  f.task_id === file.task_id ? { ...f, status: 'SUCCESS' } : f
                )
              );
              // Notify user in chat
              addMessage({
                sender: 'bot',
                text: `✅ File "${file.file_name}" has been processed and is ready.`,
              });
            } else if (response.data.status === 'FAILURE') {
                // Handle failure case
            }
          } catch (error) {
            console.error(`Failed to get status for task ${file.task_id}`, error);
          }
        }
      });
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [processingFiles, addMessage]);

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
    <Layout onFileUpload={handleFileUpload}>
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
