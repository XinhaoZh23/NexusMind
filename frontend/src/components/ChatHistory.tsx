import React from 'react';
import { Avatar, Box, Paper, Stack, Typography } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import type { Message } from '../App'; // Import the Message type from App.tsx

interface ChatHistoryProps {
  messages: Message[];
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  return (
    <Stack spacing={2} sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
      {messages.map((message) => (
        <Box
          key={message.id}
          sx={{
            display: 'flex',
            justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 2,
              maxWidth: '70%',
              bgcolor: message.sender === 'user' ? 'primary.main' : 'background.paper',
              color: message.sender === 'user' ? 'primary.contrastText' : 'text.primary',
            }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Avatar sx={{ bgcolor: message.sender === 'user' ? 'secondary.main' : 'info.main' }}>
                {message.sender === 'user' ? <PersonIcon /> : <SmartToyIcon />}
              </Avatar>
              <Typography variant="body1">{message.text}</Typography>
            </Stack>
          </Paper>
        </Box>
      ))}
    </Stack>
  );
};

export default ChatHistory;
