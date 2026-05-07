import React from 'react';
import ReactDOM from 'react-dom/client';
import { initCsrf } from './api/client';
import reportWebVitals from './reportWebVitals';
import './index.css';
import './i18n';
import App from './App';

// Fetch CSRF token before rendering so it's ready for the first request
initCsrf();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals();
