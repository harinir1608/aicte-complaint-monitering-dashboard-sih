import { useCallback, useRef, useState } from "react";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  maxSizeMb?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  existingFiles?: { name: string; size: number }[];
  onRemoveExisting?: (index: number) => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function FileUpload({
  onFilesSelected,
  accept = ".pdf,.doc,.docx,.jpg,.jpeg,.png",
  maxSizeMb = 10,
  multiple = false,
  disabled = false,
  className,
  existingFiles = [],
  onRemoveExisting,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndAdd = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      const validFiles: File[] = [];
      const newErrors: string[] = [];

      for (const file of fileArray) {
        if (file.size > maxSizeMb * 1024 * 1024) {
          newErrors.push(`"${file.name}" exceeds ${maxSizeMb} MB limit.`);
          continue;
        }
        validFiles.push(file);
      }

      setErrors(newErrors);

      if (validFiles.length > 0) {
        const updated = multiple ? [...selectedFiles, ...validFiles] : validFiles;
        setSelectedFiles(updated);
        onFilesSelected(updated);
      }
    },
    [maxSizeMb, multiple, selectedFiles, onFilesSelected]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (!disabled) validateAndAdd(e.dataTransfer.files);
    },
    [disabled, validateAndAdd]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) validateAndAdd(e.target.files);
    e.target.value = "";
  };

  const removeSelected = (index: number) => {
    const updated = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updated);
    onFilesSelected(updated);
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Drop zone */}
      <div
        className={cn(
          "relative flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6 transition-colors",
          isDragging ? "border-indigo-400 bg-indigo-50" : "border-gray-300 bg-gray-50",
          disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:border-indigo-400 hover:bg-indigo-50"
        )}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <Upload className="h-8 w-8 text-gray-400" />
        <div className="text-center">
          <p className="text-sm font-medium text-gray-700">
            Drag & drop files here, or click to browse
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Accepted: {accept} &bull; Max size: {maxSizeMb} MB
            {multiple && " • Multiple files allowed"}
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={handleChange}
          className="hidden"
        />
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="space-y-1">
          {errors.map((err, i) => (
            <div key={i} className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {err}
            </div>
          ))}
        </div>
      )}

      {/* Existing files */}
      {existingFiles.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Existing files</p>
          {existingFiles.map((file, i) => (
            <div key={i} className="flex items-center gap-3 rounded-md border border-gray-200 bg-white px-3 py-2">
              <FileText className="h-4 w-4 text-gray-400 shrink-0" />
              <span className="flex-1 text-sm text-gray-700 truncate">{file.name}</span>
              <span className="text-xs text-gray-400">{formatBytes(file.size)}</span>
              {onRemoveExisting && (
                <button onClick={() => onRemoveExisting(i)} className="text-gray-400 hover:text-red-500 transition-colors">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Newly selected files */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Selected files</p>
          {selectedFiles.map((file, i) => (
            <div key={i} className="flex items-center gap-3 rounded-md border border-indigo-200 bg-indigo-50 px-3 py-2">
              <FileText className="h-4 w-4 text-indigo-500 shrink-0" />
              <span className="flex-1 text-sm text-gray-700 truncate">{file.name}</span>
              <span className="text-xs text-gray-400">{formatBytes(file.size)}</span>
              <button onClick={() => removeSelected(i)} className="text-gray-400 hover:text-red-500 transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
