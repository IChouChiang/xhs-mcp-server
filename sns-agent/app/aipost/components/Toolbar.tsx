import React, { useRef, useState } from 'react';
import { Type, Image, Pencil, Trash2, Layers, Send, Menu, RotateCcw } from 'lucide-react';
import AlignmentMenu from './AlignmentMenu';

interface ToolbarProps {
  onAddElement: (type: 'text' | 'image' | 'drawing', content: any) => void;
  selectedElementsCount: number;
  totalElementsCount: number;
  onAlign: (alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => void;
  onDistribute: (direction: 'horizontal' | 'vertical') => void;
  onDeleteSelected: () => void;
  onLayerAction: (action: 'bringToFront' | 'sendToBack') => void;
  onPublish: () => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}

export default function Toolbar({
  onAddElement,
  selectedElementsCount,
  totalElementsCount,
  onAlign,
  onDistribute,
  onDeleteSelected,
  onLayerAction,
  onPublish,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
}: ToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showDrawingModal, setShowDrawingModal] = useState(false);
  const buttonBase =
    'flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all border border-white/30 bg-white/15 text-white hover:bg-white/25 active:scale-[0.99] shadow-[0_8px_24px_-14px_rgba(0,0,0,0.35)] backdrop-blur';

  const handleAddText = () => {
    onAddElement('text', 'Double click to edit');
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        onAddElement('image', event.target?.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAddDrawing = () => {
    setShowDrawingModal(true);
  };

  const handleDrawingComplete = (dataUrl: string) => {
    onAddElement('drawing', dataUrl);
    setShowDrawingModal(false);
  };

  return (
    <>
      <div className="relative bg-gradient-to-r from-emerald-500 via-green-500 to-lime-400 px-4 py-3 flex items-center gap-3 shadow-[0_18px_46px_-28px_rgba(16,185,129,0.55)]">
        <div className="flex items-center gap-2 rounded-full bg-white/15 px-3 py-2 text-white font-semibold">
          <Menu className="w-5 h-5" />
          <span>AI Post Designer</span>
        </div>
        
        <div className="flex items-center gap-2 pl-2">
          <button onClick={handleAddText} className={buttonBase}>
            <Type className="w-4 h-4" />
            Add Text
          </button>
          
          <button onClick={() => fileInputRef.current?.click()} className={buttonBase}>
            <Image className="w-4 h-4" />
            Add Image
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          
          <button onClick={handleAddDrawing} className={buttonBase}>
            <Pencil className="w-4 h-4" />
            Draw
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onUndo}
              disabled={!canUndo}
              className={`${buttonBase} border-white/40 disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100`}
              title="Undo"
            >
              <RotateCcw className="w-4 h-4" />
              Undo
            </button>
            <button
              onClick={onRedo}
              disabled={!canRedo}
              className={`${buttonBase} border-white/40 disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100`}
              title="Redo"
            >
              <RotateCcw className="w-4 h-4 rotate-180" />
              Redo
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 pl-4">
          <button
            onClick={onDeleteSelected}
            disabled={selectedElementsCount === 0}
            className={`${buttonBase} border-red-200/70 text-red-50 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100`}
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>

          <div className="relative">
            <details className="group">
              <summary className={`${buttonBase} cursor-pointer`}>
                <Layers className="w-4 h-4" />
                Layers
              </summary>
              <div className="absolute z-20 mt-2 w-44 rounded-lg border border-slate-200 bg-white shadow-lg p-2 space-y-1">
                <button
                  className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm"
                  onClick={() => onLayerAction('bringToFront')}
                  disabled={selectedElementsCount === 0}
                >
                  Bring to front
                </button>
                <button
                  className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm"
                  onClick={() => onLayerAction('sendToBack')}
                  disabled={selectedElementsCount === 0}
                >
                  Send to back
                </button>
              </div>
            </details>
          </div>
        </div>

        <div className="ml-auto">
          <button
            onClick={onPublish}
            disabled={totalElementsCount === 0}
            className={`${buttonBase} bg-white text-emerald-600 hover:bg-emerald-50 border-white/40 shadow-[0_10px_30px_-18px_rgba(16,185,129,0.7)] disabled:bg-white/30 disabled:text-white/70 disabled:cursor-not-allowed`}
          >
            <Send className="w-4 h-4" />
            Publish
          </button>
        </div>

        {/* Alignment Menu */}
        <AlignmentMenu 
          selectedCount={selectedElementsCount}
          onAlign={onAlign}
          onDistribute={onDistribute}
        />
      </div>

      {showDrawingModal && (
        <DrawingModal
          onClose={() => setShowDrawingModal(false)}
          onComplete={handleDrawingComplete}
        />
      )}
    </>
  );
}

interface DrawingModalProps {
  onClose: () => void;
  onComplete: (dataUrl: string) => void;
}

function DrawingModal({ onClose, onComplete }: DrawingModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState('#000000');
  const [lineWidth, setLineWidth] = useState(3);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsDrawing(true);
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const handleDone = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL();
    onComplete(dataUrl);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
        <h2 className="mb-4">Draw Your Doodle</h2>
        
        <div className="flex gap-4 mb-4">
          <div className="flex items-center gap-2">
            <label className="text-gray-700">Color:</label>
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="w-12 h-8 rounded cursor-pointer"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-gray-700">Size:</label>
            <input
              type="range"
              min="1"
              max="20"
              value={lineWidth}
              onChange={(e) => setLineWidth(Number(e.target.value))}
              className="w-32"
            />
            <span className="text-gray-600">{lineWidth}px</span>
          </div>
          
          <button
            onClick={clearCanvas}
            className="ml-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Clear
          </button>
        </div>
        
        <canvas
          ref={canvasRef}
          width={600}
          height={400}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          className="border-2 border-gray-300 rounded-lg cursor-crosshair bg-white w-full"
          style={{ maxWidth: '100%', height: 'auto' }}
        />
        
        <div className="flex gap-2 mt-4 justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleDone}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Add to Canvas
          </button>
        </div>
      </div>
    </div>
  );
}
