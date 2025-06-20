import { useState, useCallback } from 'react'
import { Upload as UploadIcon, File, X, CheckCircle } from 'lucide-react'
import axios from 'axios'

interface UploadResponse {
  message: string
  file_id: string
  total_posts: number
  processing_status: string
}

export default function Upload() {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploading(true)
    setError(null)
    setUploadResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const resetUpload = () => {
    setUploadResult(null)
    setError(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Data</h1>
        <p className="text-gray-600">Upload your social media data files for analysis</p>
      </div>

      {!uploadResult && !error && (
        <div className="card">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              isDragOver
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-4">
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="mt-2 block text-sm font-medium text-gray-900">
                  Drop files here or click to upload
                </span>
                <span className="mt-1 block text-xs text-gray-500">
                  JSON, CSV, or ZIP files up to 100MB
                </span>
              </label>
              <input
                id="file-upload"
                name="file-upload"
                type="file"
                className="sr-only"
                accept=".json,.csv,.zip"
                onChange={handleFileSelect}
                disabled={uploading}
              />
            </div>
          </div>

          {uploading && (
            <div className="mt-4 text-center">
              <div className="inline-flex items-center px-4 py-2 text-sm text-blue-700 bg-blue-100 rounded-lg">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
                Uploading and processing...
              </div>
            </div>
          )}
        </div>
      )}

      {uploadResult && (
        <div className="card">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-500 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Upload Successful!</h3>
              <p className="text-gray-600">{uploadResult.message}</p>
            </div>
          </div>
          
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-gray-600">File ID</p>
              <p className="text-lg font-semibold text-gray-900">{uploadResult.file_id}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-gray-600">Total Posts</p>
              <p className="text-lg font-semibold text-gray-900">{uploadResult.total_posts}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-gray-600">Status</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">{uploadResult.processing_status}</p>
            </div>
          </div>

          <div className="mt-6 flex space-x-3">
            <button
              onClick={resetUpload}
              className="btn-secondary"
            >
              Upload Another File
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="card">
          <div className="flex items-center">
            <X className="h-8 w-8 text-red-500 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Upload Failed</h3>
              <p className="text-gray-600">{error}</p>
            </div>
          </div>
          
          <div className="mt-6">
            <button
              onClick={resetUpload}
              className="btn-secondary"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* File Format Guide */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Supported File Formats</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <File className="h-5 w-5 text-blue-500 mr-2" />
              <span className="font-medium">JSON</span>
            </div>
            <p className="text-sm text-gray-600">
              Structured data with posts array or object containing posts
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <File className="h-5 w-5 text-green-500 mr-2" />
              <span className="font-medium">CSV</span>
            </div>
            <p className="text-sm text-gray-600">
              Comma-separated values with headers for each field
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <File className="h-5 w-5 text-purple-500 mr-2" />
              <span className="font-medium">ZIP</span>
            </div>
            <p className="text-sm text-gray-600">
              Archive containing data files and media assets
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 