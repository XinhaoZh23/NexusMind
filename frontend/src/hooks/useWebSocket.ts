import { useState, useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { Message } from '../App'; // Correctly import as a type

// The URL of our WebSocket gateway
const SOCKET_URL = 'http://localhost:8080';

// Create the socket instance outside the component to prevent re-creation on re-renders.
// This is a common pattern to avoid issues with React's strict mode and HMR.
const socket: Socket = io({
  transports: ['websocket'], // Use WebSocket transport
  // Explicitly set the path to match the Vite proxy config.
  // This prevents the client from incorrectly guessing the path (e.g., adding /api).
  path: '/socket.io/',
});

export const useWebSocket = (addMessage: (message: Omit<Message, 'id'>) => void) => {
  const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    // Connect to the WebSocket server
    // We use the '/api' path that we configured in vite.config.ts proxy
    // The socket instance is now global, so we don't need to re-connect here.
    // We only need to set up event listeners.

    // Event listener for successful connection
    socket.on('connect', () => {
      console.log('WebSocket connected successfully!');
      setIsConnected(true);
    });

    // Event listener for disconnection
    socket.on('disconnect', () => {
      console.log('WebSocket disconnected.');
      setIsConnected(false);
    });

    // Event listener for incoming messages from the server
    socket.on('message', (data: any) => {
      console.log('Message received from server:', data);
      
      let messageText: string;
      // Check if the data object has an 'answer' property for successful responses
      if (data && data.answer) {
        messageText = data.answer;
      } 
      // Check for our specific error format from the gateway
      else if (data && data.error) {
        messageText = `Error: ${data.details || data.error}`;
      }
      // Fallback for any other unexpected format
      else {
        messageText = JSON.stringify(data);
      }

      const serverMessage: Omit<Message, 'id'> = {
        sender: 'bot',
        text: messageText,
      };
      addMessage(serverMessage);
    });

    // Cleanup on component unmount
    return () => {
      // We should remove the event listeners to avoid memory leaks
      // and duplicate event handlers on re-renders.
      // We should NOT disconnect the socket itself, as the instance is shared.
      socket.off('connect');
      socket.off('disconnect');
      socket.off('message');
    };
  }, [addMessage]);

  const sendMessage = useCallback((messageText: string, brainId: string | null) => {
    if (socket && socket.connected) {
      if (!brainId) {
        console.error('No brain selected, cannot send message.');
        addMessage({ sender: 'bot', text: 'Please select a brain before sending a message.' });
        return;
      }
      console.log(`Sending message to server for brain ${brainId}:`, messageText);
      socket.emit('message', {
        type: 'qna',
        payload: {
          question: messageText,
          brain_id: brainId,
        },
      });
    } else {
      console.error('Socket not connected, cannot send message.');
    }
  }, []);

  return { isConnected, sendMessage };
};
