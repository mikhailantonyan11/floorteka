const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'data', 'stick.json');

// CORS if you preview from another origin (optional)
const cors = require('cors');
app.use(cors());

// Раздача статических файлов (HTML/CSS/JS/ images)
app.use(express.static(path.join(__dirname, 'public')));

// API: получить все клюшки
app.get('/api/sticks', (req, res) => {
  fs.readFile(DATA_FILE, 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Cannot read data file' });
    try {
      const sticks = JSON.parse(data);
      res.json(sticks);
    } catch (e) {
      res.status(500).json({ error: 'Invalid data file' });
    }
  });
});

// API: получить клюшку по id
app.get('/api/sticks/:id', (req, res) => {
  fs.readFile(DATA_FILE, 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Cannot read data file' });
    try {
      const sticks = JSON.parse(data);
      const item = sticks.find(s => String(s.id) === String(req.params.id));
      if (!item) return res.status(404).json({ error: 'Not found' });
      res.json(item);
    } catch (e) {
      res.status(500).json({ error: 'Invalid data file' });
    }
  });
});

// Fallback: serve index.html for unknown GET (optional for SPA)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server started on http://localhost:${PORT}`);
});
