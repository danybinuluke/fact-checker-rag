import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Send, CheckCircle2, XCircle, HelpCircle, Loader2, FileText, ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';
import { GlassPanel } from './GlassPanel';
import type { VerifyClaimResponse } from '@/lib/types';

export function VerificationTab() {
  const [claimText, setClaimText] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<VerifyClaimResponse | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleVerify = async () => {
    if (!claimText.trim()) return;
    
    setIsVerifying(true);
    setResult(null);
    try {
      const res = await api.verifyClaim(claimText);
      setResult(res);
    } catch (error) {
      console.error('Verification failed', error);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadSuccess(null);
    try {
      const res = await api.uploadDocument(file);
      setUploadSuccess(`Successfully indexed "${file.name}" into the knowledge base`);
    } catch (error) {
      console.error('Upload failed', error);
      setUploadSuccess(`Failed to upload "${file.name}"`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
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
    <div className="flex flex-col h-full max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-3xl font-bold mb-2">Claim Verification</h2>
          <p className="text-gray-400">Verify statements against your indexed knowledge base.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Section */}
        <GlassPanel className="md:col-span-1 flex flex-col justify-center items-center text-center border-dashed border-2 hover:border-blue-500/50 transition-colors cursor-pointer group"
          onClick={() => fileInputRef.current?.click()}
        >
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept=".txt,.pdf,.docx" 
          />
          {isUploading ? (
            <Loader2 className="w-10 h-10 text-blue-400 animate-spin mb-4" />
          ) : (
            <Upload className="w-10 h-10 text-gray-500 group-hover:text-blue-400 transition-colors mb-4" />
          )}
          <h3 className="font-medium text-lg mb-1">Add Knowledge</h3>
          <p className="text-sm text-gray-400">Upload documents to expand your RAG database</p>
          
          <AnimatePresence>
            {uploadSuccess && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-4 text-sm text-blue-400 bg-blue-500/10 px-3 py-2 rounded-lg border border-blue-500/20"
              >
                {uploadSuccess}
              </motion.div>
            )}
          </AnimatePresence>
        </GlassPanel>

        {/* Chat / Input Section */}
        <div className="md:col-span-2 flex flex-col space-y-6">
          <GlassPanel className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto mb-4 min-h-[200px] flex flex-col justify-end">
              <AnimatePresence mode="wait">
                {result ? (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`p-6 rounded-xl border ${getStatusConfig(result.verification_status).bg} ${getStatusConfig(result.verification_status).border}`}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      {(() => {
                        const Icon = getStatusConfig(result.verification_status).icon;
                        return <Icon className={`w-8 h-8 ${getStatusConfig(result.verification_status).color}`} />;
                      })()}
                      <h3 className={`text-2xl font-bold ${getStatusConfig(result.verification_status).color}`}>
                        {result.verification_status}
                      </h3>
                      <span className="ml-auto text-sm text-gray-400 bg-black/20 px-3 py-1 rounded-full">
                        Confidence: {(result.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Reasoning</h4>
                        <p className="text-gray-200 leading-relaxed">{result.explanation}</p>
                      </div>
                      
                      {(result.supporting_evidence?.length > 0 || result.contradicting_evidence?.length > 0) && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Evidence Retrieved</h4>
                          <ul className="space-y-2">
                            {result.supporting_evidence?.map((evidence, i) => (
                              <li key={`sup-${i}`} className="flex gap-3 text-sm bg-black/20 p-3 rounded-lg border border-white/5">
                                <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                                <span className="text-gray-300">{evidence}</span>
                              </li>
                            ))}
                            {result.contradicting_evidence?.map((evidence, i) => (
                              <li key={`con-${i}`} className="flex gap-3 text-sm bg-black/20 p-3 rounded-lg border border-white/5">
                                <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                                <span className="text-gray-300">{evidence}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="h-full flex flex-col items-center justify-center text-gray-500"
                  >
                    <ShieldCheck className="w-16 h-16 mb-4 opacity-20" />
                    <p>Enter a claim below to verify it against the database.</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Input area */}
            <div className="relative">
              <input
                type="text"
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleVerify()}
                placeholder="Enter a claim to verify... (e.g., Apple was founded in 1975)"
                className="w-full bg-black/40 border border-white/10 rounded-xl py-4 pl-4 pr-14 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
              <button
                onClick={handleVerify}
                disabled={!claimText.trim() || isVerifying}
                className="absolute right-2 top-2 p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isVerifying ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </GlassPanel>
        </div>
      </div>
    </div>
  );
}
