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

const drawerWidth = 280;

// Dummy data for presentation
const dummyFiles = [
  { id: '1', name: 'annual_report_2023.pdf' },
  { id: '2', name: 'project_alpha_requirements.docx' },
  { id: '3', name: 'market_analysis_q4.xlsx' },
];

interface File {
  id: string;
  name: string;
}

// For now, we are not using props, but defining them for future use.
interface FileExplorerProps {
  files?: File[];
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onDeleteFile?: (fileId: string) => void;
}

const FileExplorer: React.FC<FileExplorerProps> = () => {
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
        {dummyFiles.map((file) => (
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
            <ListItemText primary={file.name} sx={{ wordBreak: 'break-all' }}/>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default FileExplorer; 