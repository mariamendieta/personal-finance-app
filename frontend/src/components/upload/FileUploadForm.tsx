"use client";

import { useCallback, useState } from "react";

interface UploadSlot {
  label: string;
  filePrefix: string;
}

interface FileUploadFormProps {
  title: string;
  slots: UploadSlot[];
  onFilesSelected: (files: Map<string, File>) => void;
}

export default function FileUploadForm({ title, slots, onFilesSelected }: FileUploadFormProps) {
  const [selectedFiles, setSelectedFiles] = useState<Map<string, File>>(new Map());

  const handleFileChange = useCallback((prefix: string, file: File | null) => {
    setSelectedFiles(prev => {
      const next = new Map(prev);
      if (file) {
        next.set(prefix, file);
      } else {
        next.delete(prefix);
      }
      onFilesSelected(next);
      return next;
    });
  }, [onFilesSelected]);

  return (
    <div>
      <h3 className="font-[Lora,serif] text-lg text-warm-charcoal mb-3">{title}</h3>
      <div className="grid grid-cols-1 gap-3">
        {slots.map(({ label, filePrefix }) => (
          <div key={filePrefix} className="flex items-center gap-4">
            <label className="text-sm text-stone w-48 shrink-0">{label}</label>
            <input
              type="file"
              accept=".csv"
              onChange={e => handleFileChange(filePrefix, e.target.files?.[0] || null)}
              className="text-sm text-warm-charcoal file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
            />
            {selectedFiles.has(filePrefix) && (
              <span className="text-xs text-verde-hoja">&#10003;</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
