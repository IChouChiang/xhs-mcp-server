import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import CanvasElement from './CanvasElement';
import { CanvasElement as CanvasElementType } from '../App';

interface CanvasProps {
  elements: CanvasElementType[];
  selectedElementIds: string[];
  onSelectElement: (id: string, isMultiSelect: boolean) => void;
  onClearSelection: () => void;
  onUpdateElement: (id: string, updates: Partial<CanvasElementType>) => void;
  onUpdateElementInstant: (id: string, updates: Partial<CanvasElementType>) => void;
  onInteractionStart: () => void;
  onViewportChange: (viewport: { centerX: number; centerY: number }) => void;
  editingResetKey: number;
}

export default function Canvas({
  elements,
  selectedElementIds,
  onSelectElement,
  onClearSelection,
  onUpdateElement,
  onUpdateElementInstant,
  onInteractionStart,
  onViewportChange,
  editingResetKey,
}: CanvasProps) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Update viewport center whenever position or scale changes
  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = (rect.width / 2 - position.x) / scale;
      const centerY = (rect.height / 2 - position.y) / scale;
      onViewportChange({ centerX, centerY });
    }
  }, [position, scale, onViewportChange]);

  // Initialize viewport on mount
  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      onViewportChange({ centerX, centerY });
    }
  }, []);

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClearSelection();
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.min(Math.max(0.1, scale * delta), 3);
    
    // Zoom towards mouse position
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      const scaleChange = newScale - scale;
      setPosition({
        x: position.x - (mouseX - position.x) * (scaleChange / scale),
        y: position.y - (mouseY - position.y) * (scaleChange / scale),
      });
    }
    
    setScale(newScale);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    // Start panning with middle mouse button or when clicking on background
    if (e.button === 1 || e.currentTarget === containerRef.current) {
      setIsPanning(true);
      setPanStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y,
      });
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isPanning) {
      setPosition({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleZoomIn = () => {
    setScale(Math.min(scale * 1.2, 3));
  };

  const handleZoomOut = () => {
    setScale(Math.max(scale * 0.8, 0.1));
  };

  const handleResetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  useEffect(() => {
    if (isPanning) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isPanning, panStart]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      {/* Zoom Controls */}
      <div className="absolute top-4 left-4 z-20 flex flex-col gap-2 bg-white rounded-lg shadow-lg p-2">
        <button
          onClick={handleZoomIn}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-5 h-5 text-gray-700" />
        </button>
        <div className="text-center text-sm text-gray-600 px-2">
          {Math.round(scale * 100)}%
        </div>
        <button
          onClick={handleZoomOut}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-5 h-5 text-gray-700" />
        </button>
        <div className="border-t border-gray-200 my-1" />
        <button
          onClick={handleResetView}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Reset View"
        >
          <Maximize2 className="w-5 h-5 text-gray-700" />
        </button>
      </div>

      {/* Canvas Container - Full Screen */}
      <div
        ref={containerRef}
        className="flex-1 relative bg-white overflow-hidden"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        style={{
          cursor: isPanning ? 'grabbing' : 'default',
        }}
      >
        {/* Content Layer - Transformable */}
        <div
          className="absolute"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: '0 0',
            left: 0,
            top: 0,
            width: '10000px',
            height: '10000px',
          }}
          onClick={handleCanvasClick}
        >
          {/* Canvas elements */}
          {elements.map((element) => (
            <CanvasElement
              key={element.id}
              element={element}
              isSelected={selectedElementIds.includes(element.id)}
              editingResetKey={editingResetKey}
              onSelect={(isMultiSelect) => onSelectElement(element.id, isMultiSelect)}
              onUpdate={onUpdateElement}
              onUpdateInstant={onUpdateElementInstant}
              onInteractionStart={onInteractionStart}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
