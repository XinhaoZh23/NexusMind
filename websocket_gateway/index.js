const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const axios = require('axios');

const app = express();
const server = http.createServer(app);

// Initialize Socket.IO server with CORS configuration
const io = new Server(server, {
  cors: {
    origin: "*", // Allow all origins for debugging purposes
    methods: ["GET", "POST"]
  }
});

const FASTAPI_URL = 'http://localhost:8000/chat';
const API_KEY = 'your-super-secret-key'; // Use the correct API key

// Listen for new connections
io.on('connection', (socket) => {
  console.log(`✅ Client connected: ${socket.id}`);

  // Listen for 'message' events from this client
  socket.on('message', async (data) => {
    console.log(`[Socket ${socket.id}] Received message:`, data);

    try {
      const requestPayload = {
        question: data.payload.question,
        // For now, we hardcode the brain_id as we did in the file upload
        brain_id: '00000000-0000-0000-0000-000000000001', 
      };

      console.log(`[Socket ${socket.id}] Forwarding to FastAPI:`, requestPayload);

      const response = await axios.post(FASTAPI_URL, requestPayload, {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json',
        },
      });

      console.log(`[Socket ${socket.id}] Received from FastAPI:`, response.data);

      // Send the response back to the original client
      socket.emit('message', response.data);

    } catch (error) {
      const errorMessage = error.response ? error.response.data : error.message;
      console.error(`[Socket ${socket.id}] Error forwarding to FastAPI:`, errorMessage);
      
      socket.emit('message', { 
        error: 'Failed to get response from backend.',
        details: errorMessage 
      });
    }
  });

  // Listen for client disconnection
  socket.on('disconnect', (reason) => {
    console.log(`❌ Client disconnected: ${socket.id}. Reason: ${reason}`);
  });

  // Listen for any connection errors
  socket.on('connect_error', (err) => {
    console.error(`Connection error for socket ${socket.id}: ${err.message}`);
  });
});

const PORT = 8080;
server.listen(PORT, () => {
  console.log(`Gateway server with Socket.IO is listening on port ${PORT}`);
}); 