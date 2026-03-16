import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryDocuments = async (question, topK = 5, temperature = 0.7) => {
  const response = await apiClient.post('/query', {
    question,
    top_k: topK,
    temperature,
  });
  return response.data;
};

export const triggerFullReindex = async () => {
  const response = await apiClient.post('/index/full');
  return response.data;
};

export const triggerIncrementalIndex = async () => {
  const response = await apiClient.post('/index/incremental');
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/index/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getIndexStats = async () => {
  const response = await apiClient.get('/index/stats');
  return response.data;
};

export const getIndexedDocuments = async () => {
  const response = await apiClient.get('/index/documents');
  return response.data;
};

export const deleteIndexedDocument = async (documentId) => {
  const response = await apiClient.delete(`/index/documents/${documentId}`);
  return response.data;
};

export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const getLangGraph = async () => {
  const response = await apiClient.get('/orchestration/graph');
  return response.data;
};
