import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Button,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Image as ImageIcon,
  Code as CodeIcon,
  VideoLibrary as VideoIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getHealth, getStatus, listScans, getCategories, AIStatus, HealthStatus, CategoryStats, ScanListItem } from '../api/client';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [recentScans, setRecentScans] = useState<ScanListItem[]>([]);
  const [categories, setCategories] = useState<CategoryStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [healthData, statusData, scansData, categoriesData] = await Promise.all([
          getHealth(),
          getStatus(),
          listScans(5),
          getCategories(),
        ]);
        setHealth(healthData);
        setStatus(statusData);
        setRecentScans(scansData);
        setCategories(categoriesData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, React.ReactElement> = {
      documents: <DocumentIcon />,
      images: <ImageIcon />,
      code: <CodeIcon />,
      videos: <VideoIcon />,
      default: <FolderIcon />,
    };
    return icons[category.toLowerCase()] || icons.default;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Status: <Chip label={health?.status || 'Unknown'} color="success" size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Database: <Chip label={health?.database || 'Unknown'} size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  AI Provider: <Chip 
                    label={status?.ai_connected ? 'Connected' : 'Disconnected'} 
                    color={status?.ai_connected ? 'success' : 'error'} 
                    size="small" 
                  />
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Disk Space: {health?.disk_space_gb.toFixed(2)} GB free
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Memory Usage: {health?.memory_usage_percent.toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <Button variant="contained" onClick={() => navigate('/scan')} fullWidth>
                  New Scan
                </Button>
                <Button variant="outlined" onClick={() => navigate('/results')} fullWidth>
                  View Results
                </Button>
                <Button variant="outlined" onClick={() => navigate('/settings')} fullWidth>
                  Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Categories */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Categories
              </Typography>
              <List>
                {categories.length > 0 ? (
                  categories.slice(0, 5).map((cat) => (
                    <ListItem key={cat.category}>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            {getCategoryIcon(cat.category)}
                            <Typography variant="body1" textTransform="capitalize">
                              {cat.category}
                            </Typography>
                          </Box>
                        }
                        secondary={`${cat.count} files`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                    No files scanned yet. Start a new scan to see categories.
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Scans */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Scans
              </Typography>
              <List>
                {recentScans.length > 0 ? (
                  recentScans.map((scan) => (
                    <ListItem key={scan.id}>
                      <ListItemText
                        primary={scan.path}
                        secondary={`${scan.file_count} files • ${new Date(scan.timestamp).toLocaleString()}`}
                      />
                    </ListItem>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                    No scans yet. Click "New Scan" to get started.
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
