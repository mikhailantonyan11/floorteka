const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'data', 'stick.json');
const LOCAL_IMAGE_MAP = {
  'oxdog-gr.png': 'C:\\Users\\user\\.cursor\\projects\\c-Users-user-Desktop\\assets\\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_ff19f60d4264bba57e44dc56532e06ea_images_photo_2026-02-03_16-15-35-8a695a80-e3d7-4680-9edb-2555d8be34f4.png',
  'oxdog-lg.png': 'C:\\Users\\user\\.cursor\\projects\\c-Users-user-Desktop\\assets\\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_ff19f60d4264bba57e44dc56532e06ea_images_photo_2026-02-03_16-15-24-0f361cbf-b969-49ed-bd4f-21dff61c44ac.png',
  'ultimatelight-fp.png': 'C:\\Users\\user\\.cursor\\projects\\c-Users-user-Desktop\\assets\\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_ff19f60d4264bba57e44dc56532e06ea_images_photo_2026-02-03_17-33-38-eeaf0e58-8dde-407f-8f77-7823c6cf53b4.png',
  'ultimatelight-tq.png': 'C:\\Users\\user\\.cursor\\projects\\c-Users-user-Desktop\\assets\\c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_ff19f60d4264bba57e44dc56532e06ea_images_photo_2026-02-03_17-33-33-1af4b159-1b1c-4c0b-b542-87a6f5469a8c.png'
};

// CORS if you preview from another origin (optional)
const cors = require('cors');
app.use(cors());

// Раздача статических файлов (HTML/CSS/JS/ images)
app.use(express.static(path.join(__dirname, 'public')));

// Временная раздача изображений в Windows (для локального просмотра)
if (process.platform === 'win32') {
  const availableImages = Object.fromEntries(
    Object.entries(LOCAL_IMAGE_MAP).filter(([, filePath]) => fs.existsSync(filePath))
  );
  if (Object.keys(availableImages).length > 0) {
    app.get('/images/:file', (req, res) => {
      const filePath = availableImages[req.params.file];
      if (!filePath) return res.status(404).end();
      res.sendFile(filePath);
    });
  }
}

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
