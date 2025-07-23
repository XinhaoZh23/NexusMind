const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');
const axios = require('axios');

const app = express();
const server = http.createServer(app);

// Use a different port for the WebSocket gateway
const PORT = process.env.PORT || 8080;
const FASTAPI_URL = 'http://localhost:8000/chat'; // Corrected path based on main.py

const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  console.log('Client connected');

  ws.on('message', async (message) => {
    try {
      const parsedMessage = JSON.parse(message);
      console.log('Received message, forwarding to FastAPI:', parsedMessage);

      const response = await axios.post(
        FASTAPI_URL,
        parsedMessage,
        {
          headers: {
            'X-API-Key': 'your-super-secret-key'
          }
        }
      );

      // Since the response is now a single JSON object, not a stream,
      // we send it directly.
      ws.send(JSON.stringify(response.data));

    } catch (error) {
      console.error('Error forwarding message to FastAPI:', error.message);
      // It's good practice to check for error.response to provide more specific details
      if (error.response) {
        ws.send(JSON.stringify({ 
          error: `Backend error: ${error.response.status}`,
          details: error.response.data 
        }));
      } else {
        ws.send(JSON.stringify({ error: 'The backend service is currently unavailable.' }));
      }
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

server.listen(PORT, () => {
  console.log(`Gateway server listening on port ${PORT}`);
}); 