import { useState, useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { Message } from '../App'; // Correctly import as a type

// The URL of our WebSocket gateway
const SOCKET_URL = 'http://localhost:8080';

export const useWebSocket = (addMessage: (message: Omit<Message, 'id'>) => void) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to the WebSocket server
    // We use the '/api' path that we configured in vite.config.ts proxy
    const newSocket = io(SOCKET_URL, {
      path: '/api/socket.io',
      transports: ['websocket'],
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
