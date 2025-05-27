// App.jsx - Main React component for Data Science File Converter
import { useState, useRef } from 'react'
import './App.css'

function App() {
  // State hooks for file, upload status, errors, download URL, etc.
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [status, setStatus] = useState('');
  const [targetFormat, setTargetFormat] = useState('.ipynb');
  const fileInputRef = useRef();

  // Supported conversions for UI dropdown
  const formatOptions = [
    { label: 'Spyder .py → Jupyter .ipynb', value: '.ipynb', input: '.py' },
    { label: 'CSV → JSON', value: '.json', input: '.csv' },
    { label: 'CSV → Excel (.xlsx)', value: '.xlsx', input: '.csv' },
    { label: 'CSV → Parquet', value: '.parquet', input: '.csv' },
    { label: 'CSV → HDF5', value: '.hdf5', input: '.csv' },
    { label: 'JSON → CSV', value: '.csv', input: '.json' },
    { label: 'Excel (.xlsx) → CSV', value: '.csv', input: '.xlsx' },
    { label: 'Parquet → CSV', value: '.csv', input: '.parquet' },
    { label: 'HDF5 → CSV', value: '.csv', input: '.hdf5' },
  ];

  // Filter valid conversions for the uploaded file
  const getAllowedFormats = () => {
    if (!selectedFile) return [];
    const ext = selectedFile.name.split('.').pop().toLowerCase();
    return formatOptions.filter(opt => opt.input.replace('.', '') === ext);
  };

  // Handle file selection
  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setError('');
    setDownloadUrl('');
    setStatus('');
  };

  // Upload file and request conversion
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload.');
      return;
    }
    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    const allowed = getAllowedFormats();
    if (!allowed.some(opt => opt.value === targetFormat)) {
      setError('Selected target format is not valid for this file type.');
      return;
    }
    setUploading(true);
    setError('');
    setStatus('Uploading...');
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('target_format', targetFormat);
    try {
      const res = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Upload failed');
      }
      const data = await res.json();
      setStatus('Converting...');
      // Download link
      setDownloadUrl(`http://localhost:8000/download/${data.file_id}`);
      setStatus('Conversion complete!');
    } catch (err) {
      setError(err.message);
      setStatus('');
    } finally {
      setUploading(false);
    }
  };

  // Download the converted file as a blob
  const handleDownload = async () => {
    if (!downloadUrl) return;
    setStatus('Downloading...');
    try {
      const res = await fetch(downloadUrl);
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      // Try to get filename from Content-Disposition header
      let filename = 'converted_file';
      const disposition = res.headers.get('content-disposition');
      if (disposition && disposition.includes('filename=')) {
        filename = disposition.split('filename=')[1].replace(/['\"]/g, '').trim();
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setStatus('Download complete!');
    } catch (err) {
      setError(err.message);
      setStatus('');
    }
  };

  // Render the UI
  return (
    <div className="container">
      <h1>Data Science File Converter</h1>
      {/* File input */}
      <input
        type="file"
        accept={formatOptions.map(opt => opt.input).filter((v, i, arr) => arr.indexOf(v) === i).join(',')}
        onChange={handleFileChange}
        ref={fileInputRef}
        disabled={uploading}
      />
      {/* Target format dropdown */}
      <select
        value={targetFormat}
        onChange={e => setTargetFormat(e.target.value)}
        disabled={uploading || !selectedFile || getAllowedFormats().length === 0}
        style={{ margin: '0 1rem' }}
      >
        {getAllowedFormats().map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {/* Upload button */}
      <button onClick={handleUpload} disabled={uploading || !selectedFile || getAllowedFormats().length === 0}>
        {uploading ? 'Uploading...' : 'Upload & Convert'}
      </button>
      {/* Status and error messages */}
      {status && <p><b>Status:</b> {status}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {/* Download button */}
      {downloadUrl && (
        <button onClick={handleDownload} style={{ display: 'block', marginTop: 16 }}>
          Download Converted File
        </button>
      )}
    </div>
  );
}

export default App
