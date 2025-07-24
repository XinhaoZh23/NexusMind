import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import Layout from './components/Layout';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import { useWebSocket } from './hooks/useWebSocket';
import { FileUpload } from './components/FileUpload';
import type { UploadedFile } from './components/FileUpload';
import FileExplorer from './components/FileExplorer';
import { AppBar, Box, CssBaseline, Toolbar, Typography } from '@mui/material';

const leftDrawerWidth = 240;
const rightDrawerWidth = 240;

// Define a type for the message object for better type safety
export interface Message {
  id: number;
  sender: 'user' | 'bot';
  text: string;
}

// Define a type for the Brain object
export interface Brain {
  id: string;
  name: string;
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
  const [brains, setBrains] = useState<Brain[]>([]);
  const [currentBrainId, setCurrentBrainId] = useState<string | null>(null);

  const addMessage = useCallback((newMessage: Omit<Message, 'id'>) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: prevMessages.length + 1, ...newMessage },
    ]);
  }, []);

  // Fetch brains on component mount
  useEffect(() => {
    const fetchBrains = async () => {
      try {
        const response = await axios.get('/api/brains', {
          headers: {
            'X-API-Key': 'your-super-secret-key',
          },
        });
        setBrains(response.data.brains);
        // Set the first brain as the current one by default
        if (response.data.brains.length > 0) {
          setCurrentBrainId(response.data.brains[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch brains:', error);
        // You might want to add a user-facing error message here
      }
    };

    fetchBrains();
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

  const handleFileUploaded = (fileName: string) => {
    addMessage({
      sender: 'bot',
      text: `✅ File "${fileName}" has been uploaded and is being processed.`,
    });
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${leftDrawerWidth}px)`,
          ml: `${leftDrawerWidth}px`,
          zIndex: (theme) => theme.zIndex.drawer + 1
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            NEXUSMIND
          </Typography>
        </Toolbar>
      </AppBar>
      <Layout onFileUploaded={handleFileUploaded} />
      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          // Account for both drawers
          width: `calc(100% - ${leftDrawerWidth + rightDrawerWidth}px)`,
          // No longer need margin left, as the AppBar and Drawers are positioned correctly
        }}
      >
        <Toolbar /> {/* Spacer for the AppBar */}
        <ChatHistory messages={messages} />
        <MessageInput
          inputValue={inputValue}
          setInputValue={setInputValue}
          onSendMessage={handleSendMessage}
          isConnected={isConnected}
        />
      </Box>
      <FileExplorer />
    </Box>
  );
}

export default App;
