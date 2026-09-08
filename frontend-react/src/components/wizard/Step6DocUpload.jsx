import React, { useState } from 'react';
import { Camera, Upload, FileText, CheckCircle, ArrowRight, SkipForward, Loader2 } from 'lucide-react';

export default function Step6DocUpload({ onNext }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessingOcr, setIsProcessingOcr] = useState(false);
  const [ocrResults, setOcrResults] = useState([]);

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    setIsProcessingOcr(true);
    setUploadedFiles(prev => [...prev, ...files]);

    // Simulate OCR Extraction (or integrate with /api/v1/documents/upload)
    setTimeout(() => {
      setIsProcessingOcr(false);
      setOcrResults([
        {
          fileName: files[0].name,
          extractedText: "Rx: Tab Amlodipine 5mg OD, Tab Metformin 500mg BD. Past History: Hypertension (diagnosed 2021).",
          diagnoses: ["Hypertension", "Type 2 Diabetes"],
          medications: ["Amlodipine 5mg", "Metformin 500mg"]
        }
      ]);
    }, 1800);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-lg">
        
        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100/80 text-emerald-800 text-xs font-bold mb-3">
            <Camera className="w-3.5 h-3.5 text-emerald-600" />
            <span>Step 6: Document OCR</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#0d382d]">
            Upload Medical Documents or Prescriptions
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Hold prior prescriptions, test reports, or discharge slips up to the camera. Document AI extracts diagnosis history and lab values instantly.
          </p>
        </div>

        {/* Upload Dropzone */}
        <div className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-2xl p-8 sm:p-10 text-center transition-all bg-slate-50/50 hover:bg-emerald-50/20 mb-6">
          <input
            type="file"
            id="doc-upload"
            accept="image/*,application/pdf"
            multiple
            onChange={handleFileUpload}
            className="hidden"
          />
          <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center">
            <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3.5 shadow-2xs">
              <Upload className="w-7 h-7" />
            </div>
            <span className="text-base font-bold text-slate-800">
              Tap to Photograph or Browse Files
            </span>
            <span className="text-xs text-slate-500 mt-1">
              Supports JPG, PNG, PDF prescriptions &amp; lab slips
            </span>
          </label>
        </div>

        {/* OCR Processing State */}
        {isProcessingOcr && (
          <div className="flex items-center justify-center gap-3 p-4 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs sm:text-sm font-semibold mb-6 animate-pulse">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
            <span>Document AI is scanning prescription text &amp; extracting medication history...</span>
          </div>
        )}

        {/* Extracted OCR Preview Cards */}
        {ocrResults.length > 0 && (
          <div className="space-y-3 mb-6">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Document AI Extracted Summary
            </h4>
            {ocrResults.map((res, i) => (
              <div key={i} className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200">
                <div className="flex items-center gap-2 mb-2 text-emerald-900 font-bold text-sm">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>{res.fileName} — Scanned Successfully</span>
                </div>
                <p className="text-xs text-slate-700 italic bg-white p-3 rounded-xl border border-slate-200 mb-3">
                  "{res.extractedText}"
                </p>
                <div className="flex flex-wrap gap-2">
                  {res.medications.map((med, mIdx) => (
                    <span key={mIdx} className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-200/70 text-emerald-900">
                      💊 {med}
                    </span>
                  ))}
                  {res.diagnoses.map((diag, dIdx) => (
                    <span key={dIdx} className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-blue-100 text-blue-900">
                      📋 {diag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between gap-4 pt-2">
          <button
            type="button"
            onClick={() => onNext({ hasDocuments: false, ocrResults: [] })}
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-slate-500 hover:text-slate-800 cursor-pointer"
          >
            <SkipForward className="w-4 h-4" />
            <span>Skip (No documents today)</span>
          </button>

          <button
            type="button"
            onClick={() => onNext({ hasDocuments: ocrResults.length > 0, ocrResults })}
            className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-sm sm:text-base shadow-md transition-all hover:scale-102 cursor-pointer"
          >
            <span>Proceed to Clinical AI</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
}
