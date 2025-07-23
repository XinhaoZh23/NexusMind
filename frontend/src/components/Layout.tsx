import React from 'react';
import {
  AppBar, Box, CssBaseline, Drawer, Toolbar, Typography
} from '@mui/material';
import { FileUpload } from './FileUpload';
import type { UploadedFile } from './FileUpload';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
  onFileUpload: (file: UploadedFile) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, onFileUpload }) => {
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
        <FileUpload onFileUpload={onFileUpload} />
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
