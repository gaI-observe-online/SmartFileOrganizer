import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  Slider,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import { getSettings, updateSettings, Settings as SettingsType } from '../api/client';
import { useAppStore } from '../utils/store';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addNotification = useAppStore((state) => state.addNotification);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const updated = await updateSettings({
        ai_endpoint: settings.ai_endpoint,
        ai_model: settings.ai_model,
        auto_approve_threshold: settings.auto_approve_threshold,
        help_base_url: settings.help_base_url,
      });
      setSettings(updated);
      setSuccess(true);
      addNotification('success', 'Settings saved successfully');

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!settings) {
    return (
      <Box>
        <Alert severity="error">Failed to load settings</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Settings saved successfully!
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI Provider Configuration
          </Typography>

          <TextField
            fullWidth
            label="Ollama Endpoint"
            value={settings.ai_endpoint}
            onChange={(e) => setSettings({ ...settings, ai_endpoint: e.target.value })}
            margin="normal"
            helperText="URL of your Ollama instance (e.g., http://localhost:11434)"
          />

          <TextField
            fullWidth
            label="AI Model"
            value={settings.ai_model}
            onChange={(e) => setSettings({ ...settings, ai_model: e.target.value })}
            margin="normal"
            helperText="Model to use (e.g., llama3.3, qwen2.5)"
          />
        </CardContent>
      </Card>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Scan Preferences
          </Typography>

          <FormControl fullWidth margin="normal">
            <Typography gutterBottom>
              Auto-Approve Threshold: {settings.auto_approve_threshold}
            </Typography>
            <Slider
              value={settings.auto_approve_threshold}
              onChange={(_, value) =>
                setSettings({ ...settings, auto_approve_threshold: value as number })
              }
              min={0}
              max={100}
              marks={[
                { value: 0, label: '0' },
                { value: 30, label: '30' },
                { value: 70, label: '70' },
                { value: 100, label: '100' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Files with risk score below this threshold will be auto-approved
            </Typography>
          </FormControl>
        </CardContent>
      </Card>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            General Settings
          </Typography>

          <TextField
            fullWidth
            label="Database Path"
            value={settings.database_path}
            margin="normal"
            disabled
            helperText="Location of the audit database (read-only)"
          />

          <TextField
            fullWidth
            label="Server Port"
            value={settings.port}
            margin="normal"
            disabled
            helperText="Port the web server is running on (read-only)"
          />

          <TextField
            fullWidth
            label="Help Base URL"
            value={settings.help_base_url}
            onChange={(e) => setSettings({ ...settings, help_base_url: e.target.value })}
            margin="normal"
            helperText="Base URL for help documentation links"
          />
        </CardContent>
      </Card>

      <Box sx={{ mt: 3 }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>
    </Box>
  );
};

export default Settings;
