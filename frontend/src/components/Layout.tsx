import React from 'react';
import {
  Box,
  Drawer,
  Toolbar,
  Typography,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Button,
} from '@mui/material';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { FileUpload } from './FileUpload';

const drawerWidth = 240;

// Dummy data for presentation purposes
const dummyBrains = [
  { id: '1', name: 'Default Brain' },
  { id: '2', name: 'Project Alpha' },
  { id: '3', name: 'Personal Notes' },
];

interface LayoutProps {
  onFileUploaded: (fileName: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ onFileUploaded }) => {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ p: 2, pb: 1 }}>
        <Typography variant="h6" component="div">
          Brains
        </Typography>
      </Box>
      <List>
        {dummyBrains.map((brain, index) => (
          <ListItem key={brain.id} disablePadding>
            <ListItemButton selected={index === 0}>
              <ListItemIcon>
                <PsychologyIcon />
              </ListItemIcon>
              <ListItemText primary={brain.name} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ p: 2 }}>
        <Button
          variant="outlined"
          startIcon={<AddCircleOutlineIcon />}
          fullWidth
          onClick={() => alert('New Brain clicked!')}
        >
          New Brain
        </Button>
      </Box>
      <Divider sx={{ mt: 'auto' }} />
      <Box sx={{ p: 2 }}>
        <FileUpload onFileUploaded={onFileUploaded} />
      </Box>
    </Drawer>
  );
};

export default Layout;
