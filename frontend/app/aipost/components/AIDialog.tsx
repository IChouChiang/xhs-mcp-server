import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';
import { AssistantMessage, CanvasElement } from '../App';

interface AIDialogProps {
  selectedElements: CanvasElement[];
  suggestions: string[];
  onSubmit: (prompt: string, targets: CanvasElement[]) => void;
  messages: AssistantMessage[];
  onMessagesChange: (messages: AssistantMessage[]) => void;
  isLoading?: boolean;
}

export default function AIDialog({
  selectedElements,
  suggestions,
  onSubmit,
  messages,
  onMessagesChange,
  isLoading = false,
}: AIDialogProps) {
  const [prompt, setPrompt] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    // Removed check for selectedElements.length === 0 to allow AI to work without selection

    // const elementTypes = selectedElements.map(el => el.type).join(', ');
    // const responseMessage = selectedElements.length === 1
    //   ? `I'll modify your ${selectedElements[0].type} element based on your request.`
    //   : `I'll modify your ${selectedElements.length} selected elements (${elementTypes}) based on your request.`;

    onMessagesChange([
      ...messages,
      { role: 'user', content: prompt },
      // {
      //   role: 'assistant',
      //   content: responseMessage,
      // },
    ]);

    onSubmit(prompt, selectedElements);
    setPrompt('');
  };

  const singleElementSuggestions = [
    'Make it bigger',
    'Change color to blue',
    'Make it bold',
    'Rotate 45 degrees',
  ];

  const multiElementSuggestions = [
    'Align left',
    'Align top',
    'Center horizontally',
    'Distribute horizontally',
  ];

  const globalSuggestions = [
    'Add a title about Summer',
    'Search for cat images',
    'Add a red circle',
    'Create a modern layout',
  ];

  const promptCards = suggestions.length
    ? suggestions
    : selectedElements.length === 0
      ? globalSuggestions
      : selectedElements.length > 1
        ? multiElementSuggestions
        : singleElementSuggestions;

  return (
    <div className="bg-white p-4 h-full">
      <div className="h-full flex flex-col max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Sparkles className="w-5 h-5 text-emerald-500" />
            <span>Assistant</span>
          </div>

          {/* Selected Elements Context */}
          {selectedElements.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {selectedElements.slice(0, 3).map((el, index) => (
                  <div
                    key={el.id}
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 border-2 border-white flex items-center justify-center text-white text-xs"
                    title={`${el.type} element`}
                  >
                    {el.type[0].toUpperCase()}
                  </div>
                ))}
                {selectedElements.length > 3 && (
                  <div className="w-8 h-8 rounded-full bg-gray-400 border-2 border-white flex items-center justify-center text-white text-xs">
                    +{selectedElements.length - 3}
                  </div>
                )}
              </div>
              <span className="text-sm text-gray-600">
                {selectedElements.length} selected
              </span>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto mb-3 space-y-2">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
            >
              <div
                className={`max-w-md px-4 py-2 rounded-lg ${message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                  }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-lg bg-gray-100 text-gray-800">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestions */}
        <div className="mb-2">
          <div className="text-sm text-gray-600 mb-1">AI Suggestions:</div>
          <div className="flex flex-wrap gap-2">
            {promptCards.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  setPrompt(suggestion);
                }}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors text-sm text-left"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
            placeholder={
              isLoading 
                ? 'AI is thinking...' 
                : selectedElements.length > 0
                  ? 'Describe how to modify the selected elements...'
                  : 'Select elements first...'
            }
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
