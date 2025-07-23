import React, { useRef, useState } from 'react';
import axios from 'axios';
import { Box, Button, LinearProgress, Typography } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';

export interface UploadedFile {
  task_id: string;
  file_name: string;
}

interface FileUploadProps {
  onFileUpload: (file: UploadedFile) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleUploadClick = () => {
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
    formData.append('brain_id', '00000000-0000-0000-0000-000000000001');

    setIsUploading(true);
    setUploadStatus(`Uploading ${file.name}...`);

    try {
      const response = await axios.post('/upload-api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-API-Key': 'nexusmind-power-user-key',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
          );
          setUploadProgress(percentCompleted);
        },
      });
      setUploadStatus(`✅ ${response.data.message}`);
      
      // Pass the task info up to the parent component
      onFileUpload({
        task_id: response.data.task_id,
        file_name: file.name,
      });

    } catch (error) {
      console.error('File upload failed:', error);
      setUploadStatus('❌ Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
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
  );
};
