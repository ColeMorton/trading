export interface CSVFile {
  path: string;
  name: string;
}

export interface CSVData {
  data: Record<string, any>[];
  columns: string[];
}

export interface UpdateStatus {
  status: 'accepted' | 'running' | 'completed' | 'failed';
  execution_id?: string;
  progress?: number;
  error?: string;
  message?: string;
}