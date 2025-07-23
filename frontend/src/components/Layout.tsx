import React, { useState } from 'react';
import axios from 'axios';
import {
  AppBar, Box, Button, CssBaseline, Drawer, LinearProgress, Toolbar, Typography
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

const drawerWidth = 240;

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleUploadClick = () => {
    // Reset status before opening file dialog
    setUploadStatus('');
    setUploadProgress(null);
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    // Add the required brain_id field for the backend endpoint
    formData.append('brain_id', '00000000-0000-0000-0000-000000000001');

    setIsUploading(true);
    setUploadStatus(`Uploading ${file.name}...`);

    try {
      const response = await axios.post('/upload-api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-API-Key': 'nexusmind-power-user-key', // Add the required API Key
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
          );
          setUploadProgress(percentCompleted);
        },
      });
      // Use the actual message returned from the server
      setUploadStatus(`✅ ${response.data.message}`);
    } catch (error) {
      console.error('File upload failed:', error);
      setUploadStatus('❌ Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{ width: `calc(100% - ${drawerWidth}px)`, ml: `${drawerWidth}px` }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            NEXUSMIND
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar />
        <Box sx={{ p: 2 }}>
          <Button
            variant="contained"
            component="label"
            startIcon={<UploadFileIcon />}
            fullWidth
            onClick={handleUploadClick}
            disabled={isUploading}
          >
            Upload File
          </Button>
          <input
            type="file"
            hidden
            ref={fileInputRef}
            onChange={handleFileChange}
            disabled={isUploading}
          />
          {isUploading && uploadProgress !== null && (
            <Box sx={{ width: '100%', mt: 1 }}>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}
          {uploadStatus && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {uploadStatus}
            </Typography>
          )}
        </Box>
      </Drawer>
      <Box
        component="main"
        sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3 }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default Layout;
