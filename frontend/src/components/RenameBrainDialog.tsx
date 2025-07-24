import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  Button,
} from '@mui/material';
import type { Brain } from '../App';

interface RenameBrainDialogProps {
  open: boolean;
  onClose: () => void;
  onRename: (newName: string) => void;
  brain: Brain | null;
}

const RenameBrainDialog: React.FC<RenameBrainDialogProps> = ({
  open,
  onClose,
  onRename,
  brain,
}) => {
  const [name, setName] = useState('');

  useEffect(() => {
    // When the dialog opens, pre-fill the input with the current brain's name
    if (open && brain) {
      setName(brain.name);
    }
  }, [open, brain]);

  const handleRename = () => {
    if (name.trim()) {
      onRename(name.trim());
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Rename Brain</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Brain Name"
          type="text"
          fullWidth
          variant="standard"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleRename()}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleRename} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RenameBrainDialog; 