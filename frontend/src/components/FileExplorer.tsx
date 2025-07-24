import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Typography,
  Divider,
  Box,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import DeleteIcon from '@mui/icons-material/Delete';
import type { BrainFile } from '../App'; // Import the BrainFile type

const drawerWidth = 280;

interface FileExplorerProps {
  files: BrainFile[];
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onDeleteFile?: (fileId: string) => void;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ files }) => {
  return (
    <Drawer
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          // Position it below the AppBar
          top: '64px', 
          height: 'calc(100% - 64px)',
        },
      }}
      variant="permanent" // Use permanent variant for a fixed sidebar
      anchor="right"
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" component="div">
          Brain Files
        </Typography>
      </Box>
      <Divider />
      <List>
        {files.map((file) => (
          <ListItem
            key={file.id}
            secondaryAction={
              <IconButton edge="end" aria-label="delete" onClick={() => alert('Delete clicked!')}>
                <DeleteIcon />
              </IconButton>
            }
          >
            <ListItemIcon>
              <DescriptionIcon />
            </ListItemIcon>
            <ListItemText primary={file.file_name} sx={{ wordBreak: 'break-all' }}/>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default FileExplorer; 