import React from 'react';
import { IconButton, Paper, TextField } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface MessageInputProps {
  inputValue: string;
  setInputValue: (value: string) => void;
  onSendMessage: () => void;
  isConnected: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({
  inputValue,
  setInputValue,
  onSendMessage,
  isConnected,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevent form submission and page reload
    onSendMessage();
  };

  return (
    <Paper
      component="form"
      sx={{
        p: '2px 4px',
        display: 'flex',
        alignItems: 'center',
        width: '100%',
      }}
      onSubmit={handleSubmit}
    >
      <TextField
        sx={{ ml: 1, flex: 1 }}
        placeholder={isConnected ? "Ask NEXUSMIND anything..." : "Connecting..."}
        variant="standard"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        autoComplete="off"
        disabled={!isConnected}
      />
      <IconButton type="submit" sx={{ p: '10px' }} aria-label="send" disabled={!isConnected}>
        <SendIcon />
      </IconButton>
    </Paper>
  );
};

export default MessageInput;
