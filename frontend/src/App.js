import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Upload, FileText, CheckCircle, AlertCircle, X, Loader } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [historyError, setHistoryError] = useState(null);
  const [historySuccess, setHistorySuccess] = useState(null);
  const [previouslyParsed, setPreviouslyParsed] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'history'
  const [editingStatement, setEditingStatement] = useState(null);
  const [editForm, setEditForm] = useState({});

  // Auto-dismiss notifications
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        setSuccess(null);
      }, 3000); // Auto-dismiss after 3 seconds
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000); // Auto-dismiss after 5 seconds
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (historySuccess) {
      const timer = setTimeout(() => {
        setHistorySuccess(null);
      }, 3000); // Auto-dismiss after 3 seconds
      return () => clearTimeout(timer);
    }
  }, [historySuccess]);

  useEffect(() => {
    if (historyError) {
      const timer = setTimeout(() => {
        setHistoryError(null);
      }, 5000); // Auto-dismiss after 5 seconds
      return () => clearTimeout(timer);
    }
  }, [historyError]);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearFiles = () => {
    setFiles([]);
    setError(null);
    setSuccess(null);
  };

  const clearResults = () => {
    setResults([]);
    setError(null);
    setSuccess(null);
  };

  const exportToCSV = () => {
    // Use previouslyParsed data instead of results
    const dataToExport = previouslyParsed.length > 0 ? previouslyParsed : results;
    
    if (dataToExport.length === 0) {
      setHistoryError('No data to export');
      return;
    }

    // Create CSV headers
    const headers = [
      'Filename',
      'Bank',
      'Due Date',
      'Last 4 Digits',
      'Credit Limit',
      'Available Credit',
      'Statement Date',
      'Parsed Date'
    ];

    // Create CSV rows
    const csvRows = dataToExport.map(statement => [
      statement.filename || '',
      statement.bank || '',
      statement.due_date || '',
      statement.last_4_digits || '',
      statement.credit_limit || '',
      statement.available_credit || '',
      statement.statement_date || '',
      statement.parsed_at ? new Date(statement.parsed_at).toLocaleDateString() : ''
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...csvRows.map(row => row.map(field => `"${field}"`).join(','))
    ].join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `saved_statements_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setHistorySuccess('CSV file downloaded successfully!');
  };

  // Previously Parsed Functions
  const loadPreviouslyParsed = async () => {
    setLoadingHistory(true);
    setHistoryError(null);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/statements`);
      setPreviouslyParsed(response.data.data);
    } catch (error) {
      setHistoryError('Failed to load previously parsed statements');
    } finally {
      setLoadingHistory(false);
    }
  };

  const deleteStatement = async (statementId) => {
    if (!window.confirm('Are you sure you want to delete this statement?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/statements/${statementId}`);
      setPreviouslyParsed(prev => prev.filter(stmt => stmt.id !== statementId));
      setHistorySuccess('Statement deleted successfully');
    } catch (error) {
      setHistoryError('Failed to delete statement');
    }
  };

  const startEditing = (statement) => {
    setEditingStatement(statement.id);
    setEditForm({
      bank: statement.bank || '',
      due_date: statement.due_date || '',
      last_4_digits: statement.last_4_digits || '',
      credit_limit: statement.credit_limit || '',
      available_credit: statement.available_credit || '',
      statement_date: statement.statement_date || ''
    });
  };

  const cancelEditing = () => {
    setEditingStatement(null);
    setEditForm({});
  };

  const saveEdit = async (statementId) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/statements/${statementId}`, editForm);
      
      // Update the statement in the list
      setPreviouslyParsed(prev => 
        prev.map(stmt => 
          stmt.id === statementId 
            ? { ...stmt, ...response.data.data }
            : stmt
        )
      );
      
      setEditingStatement(null);
      setEditForm({});
      setHistorySuccess('Statement updated successfully');
    } catch (error) {
      setHistoryError('Failed to update statement');
    }
  };

  const handleEditChange = (field, value) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const parseSingleFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file.file);

    try {
      const response = await axios.post(`${API_BASE_URL}/parse-single`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to parse file');
    }
  };

  const parseMultipleFiles = async (files) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file.file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/parse-multiple`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to parse files');
    }
  };

  const handleParse = async () => {
    if (files.length === 0) {
      setError('Please select at least one PDF file');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let response;
      if (files.length === 1) {
        response = await parseSingleFile(files[0]);
        setResults(prev => [...prev, response.data]);
      } else {
        response = await parseMultipleFiles(files);
        setResults(prev => [...prev, ...response.data]);
      }

      // Clear uploaded files after successful parsing
      setFiles([]);
      setSuccess(`Successfully parsed ${response.data.length} file(s)`);
    } catch (error) {
      setError(error.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getBankBadgeClass = (bank) => {
    if (!bank) return 'bank-unknown';
    return `bank-${bank.toLowerCase()}`;
  };

  const formatValue = (value) => {
    if (!value || value === 'Not found') return 'Not found';
    return value;
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Credit Card Statement Parser</h1>
        <p>Upload your credit card statement PDFs to extract key information automatically</p>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <Upload size={20} />
          Upload & Parse
        </button>
        <button 
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('history');
            if (previouslyParsed.length === 0) {
              loadPreviouslyParsed();
            }
          }}
        >
          <FileText size={20} />
          Saved Statements
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="upload-section">
        <div
          {...getRootProps()}
          className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="upload-icon">
            <Upload size={48} />
          </div>
          <div className="upload-text">
            {isDragActive
              ? 'Drop the PDF files here...'
              : 'Drag & drop PDF files here, or click to select files'
            }
          </div>
          <div className="upload-subtext">
            Supports HDFC, ICICI, Kotak, Amex, and Capital One statements
          </div>
        </div>

        {files.length > 0 && (
          <div className="file-list">
            {files.map((file) => (
              <div key={file.id} className="file-item">
                <div>
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{formatFileSize(file.size)}</div>
                </div>
                <button
                  onClick={() => removeFile(file.id)}
                  className="btn btn-secondary"
                  style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="upload-buttons">
          <button
            onClick={handleParse}
            disabled={loading || files.length === 0}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <Loader className="spinner" size={16} />
                Parsing...
              </>
            ) : (
              <>
                <FileText size={16} />
                Parse Statements
              </>
            )}
          </button>
          <button
            onClick={clearFiles}
            disabled={loading}
            className="btn btn-secondary"
          >
            Clear Files
          </button>
        </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertCircle size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          <CheckCircle size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          {success}
        </div>
      )}

      {/* Results Section - Only shown in upload tab */}
      {activeTab === 'upload' && results.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h2 className="results-title">Parsing Results</h2>
            <button onClick={clearResults} className="clear-btn">
              Clear Results
            </button>
          </div>

          {results.map((result, index) => (
            <div key={index} className="result-card">
              <div className="result-header">
                <div className="filename">{result.filename}</div>
                <div className={`bank-badge ${getBankBadgeClass(result.bank)}`}>
                  {result.bank || 'Unknown'}
                </div>
              </div>

              <div className="result-fields">
                <div className="field">
                  <div className="field-label">Due Date</div>
                  <div className={`field-value ${!result.due_date ? 'not-found' : ''}`}>
                    {formatValue(result.due_date)}
                  </div>
                </div>

                <div className="field">
                  <div className="field-label">Last 4 Digits</div>
                  <div className={`field-value ${!result.last_4_digits ? 'not-found' : ''}`}>
                    {formatValue(result.last_4_digits)}
                  </div>
                </div>

                <div className="field">
                  <div className="field-label">Credit Limit</div>
                  <div className={`field-value ${!result.credit_limit ? 'not-found' : ''}`}>
                    {formatValue(result.credit_limit)}
                  </div>
                </div>

                <div className="field">
                  <div className="field-label">Available Credit</div>
                  <div className={`field-value ${!result.available_credit ? 'not-found' : ''}`}>
                    {formatValue(result.available_credit)}
                  </div>
                </div>

                <div className="field">
                  <div className="field-label">Statement Date</div>
                  <div className={`field-value ${!result.statement_date ? 'not-found' : ''}`}>
                    {formatValue(result.statement_date)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Saved Statements Section */}
      {activeTab === 'history' && (
        <div className="history-section">
          <div className="history-header">
            <h2>Saved Statements</h2>
            <div className="history-actions">
              <button 
                onClick={exportToCSV} 
                className="btn btn-primary"
                disabled={previouslyParsed.length === 0}
                style={{ marginRight: '10px' }}
              >
                <FileText size={16} />
                Export CSV
              </button>
              <button 
                onClick={loadPreviouslyParsed} 
                className="btn btn-primary"
                disabled={loadingHistory}
              >
                {loadingHistory ? (
                  <>
                    <Loader className="spinner" size={16} />
                    Loading...
                  </>
                ) : (
                  <>
                    <FileText size={16} />
                    Refresh
                  </>
                )}
              </button>
            </div>
          </div>

          {historyError && (
            <div className="error-message">
              <AlertCircle size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              {historyError}
            </div>
          )}

          {historySuccess && (
            <div className="success-message">
              <CheckCircle size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              {historySuccess}
            </div>
          )}

          {loadingHistory ? (
            <div className="loading">
              <Loader className="spinner" size={24} />
              Loading previously parsed statements...
            </div>
          ) : previouslyParsed.length === 0 ? (
            <div className="empty-state">
              <FileText size={48} style={{ color: '#9ca3af', marginBottom: '16px' }} />
              <h3>No Saved Statements</h3>
              <p>Upload and parse some statements to see them here</p>
            </div>
          ) : (
            <div className="statements-list">
              {previouslyParsed.map((statement) => (
                <div key={statement.id} className="statement-card">
                  <div className="statement-header">
                    <div className="statement-info">
                      <div className="statement-filename">{statement.filename}</div>
                      <div className="statement-meta">
                        <div className={`bank-badge ${getBankBadgeClass(statement.bank)}`}>
                          {statement.bank || 'Unknown'}
                        </div>
                        <span className="parsed-date">
                          Parsed: {new Date(statement.parsed_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="statement-actions">
                      {editingStatement === statement.id ? (
                        <>
                          <button 
                            onClick={() => saveEdit(statement.id)}
                            className="btn btn-primary"
                            style={{ marginRight: '8px', padding: '6px 12px' }}
                          >
                            Save
                          </button>
                          <button 
                            onClick={cancelEditing}
                            className="btn btn-secondary"
                            style={{ padding: '6px 12px' }}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button 
                            onClick={() => startEditing(statement)}
                            className="btn btn-primary"
                            style={{ marginRight: '8px', padding: '6px 12px' }}
                          >
                            Edit
                          </button>
                          <button 
                            onClick={() => deleteStatement(statement.id)}
                            className="btn btn-secondary"
                            style={{ padding: '6px 12px', backgroundColor: '#ef4444', color: 'white' }}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="statement-fields">
                    {editingStatement === statement.id ? (
                      // Edit mode
                      <div className="edit-fields">
                        <div className="edit-field">
                          <label>Bank</label>
                          <input 
                            type="text" 
                            value={editForm.bank}
                            onChange={(e) => handleEditChange('bank', e.target.value)}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Due Date</label>
                          <input 
                            type="text" 
                            value={editForm.due_date}
                            onChange={(e) => handleEditChange('due_date', e.target.value)}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Last 4 Digits</label>
                          <input 
                            type="text" 
                            value={editForm.last_4_digits}
                            onChange={(e) => handleEditChange('last_4_digits', e.target.value)}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Credit Limit</label>
                          <input 
                            type="text" 
                            value={editForm.credit_limit}
                            onChange={(e) => handleEditChange('credit_limit', e.target.value)}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Available Credit</label>
                          <input 
                            type="text" 
                            value={editForm.available_credit}
                            onChange={(e) => handleEditChange('available_credit', e.target.value)}
                          />
                        </div>
                        <div className="edit-field">
                          <label>Statement Date</label>
                          <input 
                            type="text" 
                            value={editForm.statement_date}
                            onChange={(e) => handleEditChange('statement_date', e.target.value)}
                          />
                        </div>
                      </div>
                    ) : (
                      // View mode
                      <div className="view-fields">
                        <div className="field">
                          <div className="field-label">Due Date</div>
                          <div className={`field-value ${!statement.due_date ? 'not-found' : ''}`}>
                            {formatValue(statement.due_date)}
                          </div>
                        </div>
                        <div className="field">
                          <div className="field-label">Last 4 Digits</div>
                          <div className={`field-value ${!statement.last_4_digits ? 'not-found' : ''}`}>
                            {formatValue(statement.last_4_digits)}
                          </div>
                        </div>
                        <div className="field">
                          <div className="field-label">Credit Limit</div>
                          <div className={`field-value ${!statement.credit_limit ? 'not-found' : ''}`}>
                            {formatValue(statement.credit_limit)}
                          </div>
                        </div>
                        <div className="field">
                          <div className="field-label">Available Credit</div>
                          <div className={`field-value ${!statement.available_credit ? 'not-found' : ''}`}>
                            {formatValue(statement.available_credit)}
                          </div>
                        </div>
                        <div className="field">
                          <div className="field-label">Statement Date</div>
                          <div className={`field-value ${!statement.statement_date ? 'not-found' : ''}`}>
                            {formatValue(statement.statement_date)}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
