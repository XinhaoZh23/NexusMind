import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import Layout from './components/Layout';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import { useWebSocket } from './hooks/useWebSocket';
import { FileUpload } from './components/FileUpload';
import type { UploadedFile } from './components/FileUpload';
import FileExplorer from './components/FileExplorer';
import RenameBrainDialog from './components/RenameBrainDialog'; // Import the new component
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

// Define a type for the File object
export interface BrainFile {
  id: string;
  file_name: string;
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
  const [files, setFiles] = useState<BrainFile[]>([]);
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [brainToRename, setBrainToRename] = useState<Brain | null>(null);

  const addMessage = useCallback((newMessage: Omit<Message, 'id'>) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: prevMessages.length + 1, ...newMessage },
    ]);
  }, []);

  const fetchBrains = async () => {
    try {
      const response = await axios.get('/api/brains', {
        headers: {
          'X-API-Key': 'your-super-secret-key',
        },
      });
      const brainsData = response.data.brains;
      setBrains(brainsData);
      return brainsData;
    } catch (error) {
      console.error('Failed to fetch brains:', error);
      return [];
    }
  };

  const fetchFilesForBrain = async (brainId: string) => {
    try {
      const response = await axios.get(`/api/brains/${brainId}/files`, {
        headers: {
          'X-API-Key': 'your-super-secret-key',
        },
      });
      setFiles(response.data.files);
    } catch (error) {
      console.error(`Failed to fetch files for brain ${brainId}:`, error);
      setFiles([]); // Reset files on error
    }
  };

  // Fetch brains on component mount
  useEffect(() => {
    const initialLoad = async () => {
      const brainsData = await fetchBrains();
      // Set the first brain as the current one and fetch its files
      if (brainsData.length > 0) {
        const firstBrainId = brainsData[0].id;
        setCurrentBrainId(firstBrainId);
        fetchFilesForBrain(firstBrainId);
      }
    };
  
    initialLoad();
  }, []);

  const handleSelectBrain = (brainId: string) => {
    setCurrentBrainId(brainId);
    fetchFilesForBrain(brainId);
  };

  const handleOpenRenameDialog = (brain: Brain) => {
    setBrainToRename(brain);
    setIsRenameDialogOpen(true);
  };

  const handleCloseRenameDialog = () => {
    setIsRenameDialogOpen(false);
    setBrainToRename(null);
  };

  const handleRenameBrain = async (newName: string) => {
    if (!brainToRename) return;

    try {
      await axios.put(
        `/api/brains/${brainToRename.id}`,
        { name: newName },
        {
          headers: {
            'X-API-Key': 'your-super-secret-key',
            'Content-Type': 'application/json',
          },
        }
      );
      // Refresh the brains list to show the new name
      await fetchBrains();
      handleCloseRenameDialog();
    } catch (error) {
      console.error('Failed to rename brain:', error);
      // Optionally, show an error message to the user
    }
  };

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

    // Start polling for the new file to appear in the list.
    const poll = setInterval(() => {
      if (currentBrainId) {
        // We fetch the files and check if the new file is present.
        // We don't update the state here directly to avoid UI flicker.
        axios.get<{ files: BrainFile[] }>(`/api/brains/${currentBrainId}/files`, {
          headers: { 'X-API-Key': 'your-super-secret-key' },
        }).then(response => {
          console.log(`[App.tsx] Polling... Trying to find filename: "${fileName}" in received files:`, response.data.files);
          const foundFile = response.data.files.find(file => file.file_name === fileName);
          if (foundFile) {
            // If the file is found, we stop polling and update the state.
            console.log(`[App.tsx] File found: ${fileName}. Stopping poll. Updating files state with:`, response.data.files);
            clearInterval(poll);
            setFiles(response.data.files);
          }
        }).catch(error => {
          console.error('Polling for files failed:', error);
          clearInterval(poll); // Stop polling on error
        });
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after a timeout (e.g., 30 seconds) to prevent infinite loops
    setTimeout(() => {
      clearInterval(poll);
    }, 30000);
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
      <Layout
        onFileUploaded={handleFileUploaded}
        brains={brains}
        currentBrainId={currentBrainId}
        onSelectBrain={handleSelectBrain}
        onOpenRenameDialog={handleOpenRenameDialog}
      />
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
      <FileExplorer files={files} />
      <RenameBrainDialog
        open={isRenameDialogOpen}
        onClose={handleCloseRenameDialog}
        onRename={handleRenameBrain}
        brain={brainToRename}
      />
    </Box>
  );
}

export default App;
