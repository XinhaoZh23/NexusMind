import React, { useRef, useState } from 'react';
import axios from 'axios';
import { Box, Button, LinearProgress, Typography } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { styled } from '@mui/material/styles';

export interface UploadedFile {
  filename: string;
}

interface FileUploadProps {
  onFileUploaded: (fileName: string) => void;
  currentBrainId: string | null; // Add the new prop here
}

const VisuallyHiddenInput = styled('input')({
  display: 'none',
});

export const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, currentBrainId }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ status: string; message: string } | null>(null);

  const handleUploadClick = () => {
    setUploadStatus(null);
    setUploadProgress(null);
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const fileName = file.name; // Get the filename here

    if (!currentBrainId) {
      setUploadStatus({ status: 'error', message: '❌ No brain selected.' });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('brain_id', currentBrainId);

    setIsUploading(true);
    setUploadStatus({ status: 'uploading', message: `Uploading ${file.name}...` });

    try {
      await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-API-Key': process.env.REACT_APP_API_KEY,
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
          );
          setUploadProgress(percentCompleted);
        },
      });
      setUploadStatus({
        status: 'success',
        message: `File '${fileName}' uploaded successfully.`, // Use the filename here
      });
      onFileUploaded(fileName); // Pass the correct filename to the callback
      // pollFileStatus(response.data.message); // This line was removed as per the edit hint
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus({ status: 'error', message: '❌ Upload failed.' });
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
      <VisuallyHiddenInput
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
          {uploadStatus.message}
        </Typography>
      )}
    </Box>
  );
};
