import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, HelpCircle, Loader2, ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';
import { GlassPanel } from './GlassPanel';
import type { VerifyClaimResponse } from '@/lib/types';
import FileUpload from './FileUpload';
import AIPrompt from './AIPrompt';

export function VerificationTab() {
  const [claimText, setClaimText] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<VerifyClaimResponse | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const handleVerify = async (text: string, model: string) => {
    if (!text.trim()) return;

    setClaimText(text);
    setIsVerifying(true);
    setResult(null);
    try {
      const res = await api.verifyClaim(text, model);
      setResult(res);
    } catch (error) {
      console.error('Verification failed', error);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUploadSuccess = async (file: File) => {
    setIsUploading(true);
    setUploadSuccess(null);
    try {
      await api.uploadDocument(file);
      setUploadSuccess(`Successfully indexed "${file.name}" into the knowledge base`);
    } catch (error) {
      console.error('Upload failed', error);
      setUploadSuccess(`Failed to upload "${file.name}"`);
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'SUPPORT': return { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' };
      case 'CONTRADICTION': return { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' };
      default: return { icon: HelpCircle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' };
    }
  };

  return (
    <div className="flex flex-col max-w-3xl mx-auto py-8">
      {/* Fact Checker Logo */}
      <div className="flex flex-col items-center justify-center mb-6 mt-4">
        <img
          src="/logo.png"
          alt="Fact Checker Logo"
          className="w-72 md:w-96 h-auto object-contain mb-3"
        />
        <p className="text-gray-400 text-center max-w-md">
          Verify statements against your indexed knowledge base or upload new documents to expand it.
        </p>
      </div>

      <div className="flex flex-col space-y-8 w-full mt-6 pb-10">
        {/* Document Upload Section */}
        <div className="w-full">
          <FileUpload
            onUploadSuccess={handleFileUploadSuccess}
            acceptedFileTypes={['.txt', '.pdf', '.docx', 'application/pdf', 'text/plain']}
            maxFileSize={50 * 1024 * 1024} // 50MB
            className="w-full max-w-2xl mx-auto"
          />
          <AnimatePresence>
            {(uploadSuccess || isUploading) && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="max-w-2xl mx-auto mt-4"
              >
                {isUploading ? (
                  <div className="flex items-center justify-center gap-2 text-sm text-blue-400 bg-blue-500/10 px-4 py-3 rounded-xl border border-blue-500/20">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing document on server...
                  </div>
                ) : (
                  <div className={`text-sm px-4 py-3 rounded-xl border ${uploadSuccess?.includes('Failed')
                    ? 'text-red-400 bg-red-500/10 border-red-500/20'
                    : 'text-green-400 bg-green-500/10 border-green-500/20'
                    }`}>
                    {uploadSuccess}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Claim Writer Section */}
        <div className="w-full max-w-2xl mx-auto space-y-6">
          <AIPrompt
            onSubmit={handleVerify}
            isVerifying={isVerifying}
            className="w-full mx-auto"
          />

          {/* Verification Results */}
          <AnimatePresence mode="wait">
            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`p-6 md:p-8 rounded-2xl border ${getStatusConfig(result.verification_status).bg} ${getStatusConfig(result.verification_status).border} backdrop-blur-xl`}
              >
                <div className="flex items-center gap-4 mb-6">
                  {(() => {
                    const Icon = getStatusConfig(result.verification_status).icon;
                    return <Icon className={`w-10 h-10 ${getStatusConfig(result.verification_status).color}`} />;
                  })()}
                  <h3 className={`text-3xl font-bold ${getStatusConfig(result.verification_status).color}`}>
                    {result.verification_status}
                  </h3>
                  <div className="ml-auto flex items-center justify-center bg-black/40 rounded-full px-4 py-1.5 border border-white/5 shadow-inner">
                    <span className="text-sm font-semibold text-gray-300">
                      Confidence: {(result.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="bg-black/20 p-5 rounded-xl border border-white/5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Reasoning</h4>
                    <p className="text-gray-200 leading-relaxed text-lg">{result.explanation}</p>
                  </div>

                  {(result.supporting_evidence?.length > 0 || result.contradicting_evidence?.length > 0) && (
                    <div>
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Evidence Retrieved</h4>
                      <ul className="space-y-3">
                        {result.supporting_evidence?.map((evidence, i) => (
                          <li key={`sup-${i}`} className="flex gap-4 text-base bg-green-500/5 p-4 rounded-xl border border-green-500/10">
                            <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                            <span className="text-gray-300 leading-relaxed">{evidence}</span>
                          </li>
                        ))}
                        {result.contradicting_evidence?.map((evidence, i) => (
                          <li key={`con-${i}`} className="flex gap-4 text-base bg-red-500/5 p-4 rounded-xl border border-red-500/10">
                            <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                            <span className="text-gray-300 leading-relaxed">{evidence}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
