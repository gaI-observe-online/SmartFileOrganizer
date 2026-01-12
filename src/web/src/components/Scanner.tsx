import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  LinearProgress,
  Chip,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { startScan, getScanProgress, pauseScan, cancelScan, connectToScanUpdates, ScanProgress } from '../api/client';
import { useAppStore } from '../utils/store';

const Scanner: React.FC = () => {
  const [path, setPath] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const addNotification = useAppStore((state) => state.addNotification);

  useEffect(() => {
    // Cleanup WebSocket on unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  const handleStartScan = async () => {
    if (!path) {
      setError('Please enter a path to scan');
      return;
    }

    setError(null);
    setScanning(true);

    try {
      const response = await startScan({
        path,
        recursive: true,
        auto_approve_threshold: 30,
      });

      setScanId(response.scan_id);
      addNotification('success', `Scan started: ${response.message}`);

      // Connect to WebSocket for real-time updates
      const websocket = connectToScanUpdates(
        response.scan_id,
        (message) => {
          if (message.type === 'progress') {
            setProgress(message.data);
          } else if (message.type === 'complete') {
            setScanning(false);
            addNotification('success', 'Scan completed!');
          } else if (message.type === 'error') {
            setError(message.data.message);
            setScanning(false);
          }
        },
        (error) => {
          console.error('WebSocket error:', error);
          // Fall back to polling
          pollProgress(response.scan_id);
        }
      );

      setWs(websocket);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan');
      setScanning(false);
    }
  };

  const pollProgress = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const prog = await getScanProgress(id);
        setProgress(prog);

        if (prog.status === 'completed' || prog.status === 'cancelled' || prog.status === 'error') {
          clearInterval(interval);
          setScanning(false);
          if (prog.status === 'completed') {
            addNotification('success', 'Scan completed!');
          }
        }
      } catch (err) {
        clearInterval(interval);
        setScanning(false);
      }
    }, 1000);
  };

  const handlePauseScan = async () => {
    if (!scanId) return;

    try {
      await pauseScan(scanId);
      addNotification('info', 'Scan paused');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to pause scan');
    }
  };

  const handleCancelScan = async () => {
    if (!scanId) return;

    try {
      await cancelScan(scanId);
      setScanning(false);
      setScanId(null);
      setProgress(null);
      if (ws) {
        ws.close();
      }
      addNotification('warning', 'Scan cancelled');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel scan');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
      running: 'primary',
      completed: 'success',
      paused: 'warning',
      cancelled: 'default',
      error: 'error',
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scan Files
      </Typography>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Directory to Scan
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              label="Directory Path"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/home/user/Downloads"
              disabled={scanning}
              helperText="Enter the full path to the directory you want to scan"
            />
            <Tooltip title="Browse">
              <IconButton>
                <FolderIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            {!scanning ? (
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={handleStartScan}
                disabled={!path}
              >
                Start Scan
              </Button>
            ) : (
              <>
                <Button
                  variant="outlined"
                  startIcon={<PauseIcon />}
                  onClick={handlePauseScan}
                  disabled={progress?.status !== 'running'}
                >
                  Pause
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<StopIcon />}
                  onClick={handleCancelScan}
                >
                  Cancel
                </Button>
              </>
            )}
          </Box>
        </CardContent>
      </Card>

      {progress && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Scan Progress</Typography>
              <Chip label={progress.status} color={getStatusColor(progress.status)} />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Scanning file {progress.processed_files}/{progress.total_files} ({progress.progress_percent.toFixed(1)}%)
            </Typography>

            <LinearProgress
              variant="determinate"
              value={progress.progress_percent}
              sx={{ height: 10, borderRadius: 5, mb: 2 }}
            />

            {progress.current_file && (
              <Typography variant="body2" color="text.secondary">
                Current file: {progress.current_file}
              </Typography>
            )}

            {progress.estimated_time_remaining && (
              <Typography variant="body2" color="text.secondary">
                Estimated time remaining: {Math.ceil(progress.estimated_time_remaining / 60)} minutes
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Scanner;
