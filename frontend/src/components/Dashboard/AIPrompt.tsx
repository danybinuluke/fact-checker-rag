"use client";

import { ArrowRight, Bot, Check, ChevronDown, Paperclip, Loader2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea";
import { cn } from "@/lib/utils";

interface AIPromptProps {
  models?: string[];
  defaultModel?: string;
  placeholder?: string;
  headerText?: string;
  headerAction?: string;
  onSubmit?: (value: string, model: string) => void;
  className?: string;
  isVerifying?: boolean;
}

const DEFAULT_MODELS = ["Gemini", "OpenRouter", "Ollama"];

export default function AIPrompt({
  models = DEFAULT_MODELS,
  defaultModel = "Gemini",
  placeholder = "Enter a claim to verify... (e.g., Apple was founded in 1975)",
  headerText = "AI Fact Verification",
  headerAction = "Verify Now",
  onSubmit,
  className,
  isVerifying = false,
}: AIPromptProps) {
  const [value, setValue] = useState("");
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 72,
    maxHeight: 300,
  });
  const [selectedModel, setSelectedModel] = useState(defaultModel);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const MODEL_ICONS: Record<string, React.ReactNode> = {
    "Gemini": (
      <svg
        height="1em"
        style={{ flex: "none", lineHeight: "1" }}
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <title>Gemini</title>
        <defs>
          <linearGradient
            id="lobe-icons-gemini-fill"
            x1="0%"
            x2="68.73%"
            y1="100%"
            y2="30.395%"
          >
            <stop offset="0%" stopColor="#1C7DFF" />
            <stop offset="52.021%" stopColor="#1C69FF" />
            <stop offset="100%" stopColor="#F0DCD6" />
          </linearGradient>
        </defs>
        <path
          d="M12 24A14.304 14.304 0 000 12 14.304 14.304 0 0012 0a14.305 14.305 0 0012 12 14.305 14.305 0 00-12 12"
          fill="url(#lobe-icons-gemini-fill)"
          fillRule="nonzero"
        />
      </svg>
    ),
    "Ollama": <Bot className="h-4 w-4 text-orange-400" />,
    "OpenRouter": (
      <svg
        className="h-4 w-4 text-purple-400"
        fill="none"
        viewBox="0 0 512 512"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g clipPath="url(#prefix__clip0_8_13)">
          <path
            clipRule="evenodd"
            d="M358.485 41.75l154.027 87.573v1.856l-155.605 86.634.362-45.162-17.514-.64c-22.592-.598-34.368.042-48.384 2.346-22.699 3.734-43.478 12.31-67.136 28.843l-46.208 32.107c-6.059 4.16-10.56 7.168-14.507 9.706l-10.987 6.87-8.469 4.992 8.213 4.906 11.307 7.211c10.155 6.699 24.96 16.981 57.621 39.808 23.68 16.533 44.438 25.109 67.136 28.843l6.4.96c14.806 1.941 29.334 2.005 60.267.704l.469-46.059 154.027 87.573v1.856l-155.605 86.656.298-39.722-13.546.469c-29.568.896-45.59.043-66.944-3.456-36.139-5.973-69.547-19.755-104.128-43.925l-46.038-32a467.072 467.072 0 00-16.106-10.624l-9.963-5.974c-5.38-3.1-10.785-6.157-16.213-9.173C62.037 314.24 12.01 301.141 0 301.141v-90.197l2.987.085c12.032-.149 62.08-13.269 81.258-23.978l21.675-12.374 9.344-5.845c9.131-5.973 22.869-15.488 57.301-39.531 34.582-24.17 67.968-37.973 104.128-43.925 24.576-4.053 42.112-4.544 81.366-2.944l.426-40.683z"
            fill="currentColor"
            fillRule="evenodd"
          />
        </g>
        <defs>
          <clipPath id="prefix__clip0_8_13">
            <path d="M0 0h512v512H0z" fill="#fff" />
          </clipPath>
        </defs>
      </svg>
    ),
  };

  const handleSubmit = () => {
    if (!value.trim() || isVerifying) return;
    onSubmit?.(value, selectedModel);
    setValue("");
    adjustHeight(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={cn("w-full py-4", className)}>
      <div className="rounded-2xl bg-black/40 border border-white/10 p-1.5 pt-4 backdrop-blur-xl shadow-2xl">
        <div className="mx-2 mb-2.5 flex items-center gap-2">
          <div className="flex flex-1 items-center gap-2">
            <Bot className="h-4 w-4 text-blue-400" />
            <h3 className="text-white/90 text-sm font-medium tracking-tighter">
              {headerText}
            </h3>
          </div>
          <p className="text-gray-400 text-xs tracking-tighter">
            {headerAction}
          </p>
        </div>
        <div className="relative">
          <div className="relative flex flex-col">
            <div className="overflow-y-auto" style={{ maxHeight: "400px" }}>
              <textarea
                className={cn(
                  "w-full resize-none rounded-xl rounded-b-none border-none bg-black/20 px-4 py-4 placeholder:text-gray-500 focus-visible:outline-none text-white",
                  "min-h-[72px]"
                )}
                id="ai-input"
                onChange={(e) => {
                  setValue(e.target.value);
                  adjustHeight();
                }}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                ref={textareaRef}
                value={value}
                disabled={isVerifying}
              />
            </div>

            <div className="flex h-14 items-center rounded-b-xl bg-black/20 border-t border-white/5 relative">
              <div className="absolute right-3 bottom-3 left-3 flex w-[calc(100%-24px)] items-center justify-between">
                <div className="flex items-center gap-2" ref={dropdownRef}>
                  <div className="relative">
                    <button
                      onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                      className="flex h-8 items-center gap-1.5 rounded-md px-2 text-xs hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-blue-500 text-white transition-colors bg-white/5"
                      type="button"
                    >
                      <AnimatePresence mode="wait">
                        <motion.div
                          animate={{ opacity: 1, y: 0 }}
                          className="flex items-center gap-1.5"
                          exit={{ opacity: 0, y: 5 }}
                          initial={{ opacity: 0, y: -5 }}
                          key={selectedModel}
                          transition={{ duration: 0.15 }}
                        >
                          {MODEL_ICONS[selectedModel] || <Bot className="h-4 w-4" />}
                          <span className="font-medium">{selectedModel}</span>
                          <ChevronDown className="h-3 w-3 opacity-50 ml-1" />
                        </motion.div>
                      </AnimatePresence>
                    </button>
                    
                    {/* Custom Dropdown */}
                    <AnimatePresence>
                      {isDropdownOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 5 }}
                          className="absolute bottom-full left-0 mb-2 min-w-[10rem] rounded-xl border border-white/10 bg-neutral-900 shadow-xl overflow-hidden z-50"
                        >
                          {models.map((model) => (
                            <button
                              key={model}
                              className="flex w-full items-center justify-between gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-white/10 transition-colors"
                              onClick={() => {
                                setSelectedModel(model);
                                setIsDropdownOpen(false);
                              }}
                            >
                              <div className="flex items-center gap-2">
                                {MODEL_ICONS[model] || <Bot className="h-4 w-4 opacity-50" />}
                                <span>{model}</span>
                              </div>
                              {selectedModel === model && (
                                <Check className="h-4 w-4 text-blue-500" />
                              )}
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
                
                <button
                  aria-label="Send message"
                  className={cn(
                    "flex items-center justify-center rounded-lg p-2 transition-all duration-200",
                    value.trim() && !isVerifying
                      ? "bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]"
                      : "bg-white/5 text-white/30 cursor-not-allowed"
                  )}
                  disabled={!value.trim() || isVerifying}
                  type="button"
                  onClick={handleSubmit}
                >
                  {isVerifying ? (
                    <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                  ) : (
                    <ArrowRight className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
