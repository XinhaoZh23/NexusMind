const express = require('express');
const http = require('http');

const app = express();
const server = http.createServer(app);

const PORT = process.env.PORT || 3001;

app.get('/', (req, res) => {
  res.send('WebSocket Gateway is running.');
});

server.listen(PORT, () => {
  console.log(`Gateway server listening on port ${PORT}`);
}); 