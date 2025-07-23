const express = require('express');
const http = require('http');
const { WebSocketServer } = require('ws');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
const server = http.createServer(app);

// Use a different port for the WebSocket gateway to avoid conflicts
const PORT = process.env.PORT || 8080;
const FASTAPI_URL = 'http://localhost:8000/chat/stream'; // Corrected port for FastAPI

const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  console.log('Client connected');

  ws.on('message', async (message) => {
    try {
      const parsedMessage = JSON.parse(message);
      console.log('Received message object =>', parsedMessage);

      const response = await axios.post(FASTAPI_URL, parsedMessage, {
        responseType: 'stream',
      });

      response.data.on('data', (chunk) => {
        // Forward each chunk of data to the client as soon as it's received
        ws.send(chunk.toString());
      });

      response.data.on('end', () => {
        console.log('Stream ended');
        // Optionally, send a special message to indicate the end of the stream
        ws.send(JSON.stringify({ type: 'stream_end' }));
      });

    } catch (error) {
      console.error('Error processing message or forwarding to FastAPI:', error.message);
      ws.send(JSON.stringify({ error: 'Failed to process your request.' }));
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