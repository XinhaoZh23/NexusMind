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
  IconButton,
} from '@mui/material';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditIcon from '@mui/icons-material/Edit'; // Import EditIcon
import PsychologyIcon from '@mui/icons-material/Psychology';
import { FileUpload } from './FileUpload';
import type { Brain } from '../App'; // Import the Brain type

const drawerWidth = 240;

interface LayoutProps {
  onFileUploaded: (fileName:string) => void;
  brains: Brain[];
  currentBrainId: string | null;
  onSelectBrain: (brainId: string) => void;
  onOpenRenameDialog: (brain: Brain) => void;
}

const Layout: React.FC<LayoutProps> = ({
  onFileUploaded,
  brains,
  currentBrainId,
  onSelectBrain,
  onOpenRenameDialog,
}) => {
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
        {brains.map((brain) => (
          <ListItem
            key={brain.id}
            disablePadding
            secondaryAction={
              <IconButton edge="end" aria-label="edit" onClick={() => onOpenRenameDialog(brain)}>
                <EditIcon />
              </IconButton>
            }
          >
            <ListItemButton
              selected={brain.id === currentBrainId}
              onClick={() => onSelectBrain(brain.id)}
            >
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
