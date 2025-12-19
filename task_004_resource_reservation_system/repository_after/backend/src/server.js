require('dotenv').config();
const express = require('express');
const cors = require('cors');
const database = require('./database/db');
const authController = require('./controllers/authController');
const resourceController = require('./controllers/resourceController');
const reservationController = require('./controllers/reservationController');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.use('/api/auth', authController);
app.use('/api/resources', resourceController);
app.use('/api/reservations', reservationController);

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

async function startServer() {
  try {
    await database.initialize();
    console.log('Database initialized');
    
    if (process.env.NODE_ENV !== 'test') {
      app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
      });
    }
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

if (process.env.NODE_ENV !== 'test') {
  startServer();
}

module.exports = app;
