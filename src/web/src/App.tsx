import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { useAppStore } from './utils/store';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Scanner from './components/Scanner';
import Results from './components/Results';
import Settings from './components/Settings';
import { getSettings } from './api/client';

function App() {
  const darkMode = useAppStore((state) => state.darkMode);
  const setSettings = useAppStore((state) => state.setSettings);

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: {
            main: '#1976d2',
          },
          secondary: {
            main: '#dc004e',
          },
        },
      }),
    [darkMode]
  );

  // Load settings on app start
  useEffect(() => {
    getSettings()
      .then((settings) => setSettings(settings))
      .catch((error) => console.error('Failed to load settings:', error));
  }, [setSettings]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan" element={<Scanner />} />
            <Route path="/results" element={<Results />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
