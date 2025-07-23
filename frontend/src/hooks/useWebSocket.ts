import { useState, useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { Message } from '../App'; // Correctly import as a type

// No hardcoded URL needed. io() will default to the current host.
// const SOCKET_URL = 'http://localhost:8080';

export const useWebSocket = (addMessage: (message: Omit<Message, 'id'>) => void) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to the WebSocket server running on the same host as the web app.
    // Vite will proxy requests to /socket.io to our gateway on port 8080.
    const newSocket = io({
      transports: ['websocket'], // Use WebSocket transport
    });

    setSocket(newSocket);

    // Event listener for successful connection
    newSocket.on('connect', () => {
      console.log('WebSocket connected successfully!');
      setIsConnected(true);
    });

    // Event listener for disconnection
    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected.');
      setIsConnected(false);
    });

    // Event listener for incoming messages from the server
    newSocket.on('message', (data: any) => {
      console.log('Message received from server:', data);
      const serverMessage: Omit<Message, 'id'> = {
        sender: 'bot',
        text: data.reply || JSON.stringify(data),
      };
      addMessage(serverMessage);
    });

    // Cleanup on component unmount
    return () => {
      console.log('Disconnecting WebSocket.');
      newSocket.disconnect();
    };
  }, [addMessage]);

  const sendMessage = useCallback((messageText: string) => {
    if (socket && socket.connected) {
      console.log('Sending message to server:', messageText);
      socket.emit('message', {
        type: 'qna',
        payload: {
          question: messageText,
        },
      });
    } else {
      console.error('Socket not connected, cannot send message.');
    }
  }, [socket]);

  return { isConnected, sendMessage };
};
