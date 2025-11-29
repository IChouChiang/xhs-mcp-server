import React, { useState, useRef, useEffect } from 'react';
import { Resizable } from 're-resizable';
import { CanvasElement as CanvasElementType } from '../App';

interface CanvasElementProps {
  element: CanvasElementType;
  isSelected: boolean;
  editingResetKey: number;
  onSelect: (isMultiSelect: boolean) => void;
  onUpdate: (id: string, updates: Partial<CanvasElementType>) => void;
  onUpdateInstant: (id: string, updates: Partial<CanvasElementType>) => void;
  onInteractionStart: () => void;
}

export default function CanvasElement({
  element,
  isSelected,
  editingResetKey,
  onSelect,
  onUpdate,
  onUpdateInstant,
  onInteractionStart,
}: CanvasElementProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isEditing, setIsEditing] = useState(false);
  const textRef = useRef<HTMLDivElement>(null);
  const pendingDragUpdate = useRef<Partial<CanvasElementType> | null>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    // Avoid starting drag when the intention is to edit via double click.
    if (element.type === 'text' && e.detail === 2) {
      onSelect(e.shiftKey || e.ctrlKey || e.metaKey);
      return;
    }

    if (isEditing) {
      // Keep selection logic while avoiding drag when editing inline.
      const isMultiSelect = e.shiftKey || e.ctrlKey || e.metaKey;
      onSelect(isMultiSelect);
      return;
    }
    e.stopPropagation();
    
    // Check for multi-select (Shift or Ctrl/Cmd key)
    const isMultiSelect = e.shiftKey || e.ctrlKey || e.metaKey;
    onSelect(isMultiSelect);
    onInteractionStart();
    
    setIsDragging(true);
    setDragStart({
      x: e.clientX - element.x,
      y: e.clientY - element.y,
    });
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;
    const next = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    };
    pendingDragUpdate.current = next;
    onUpdateInstant(element.id, next);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    if (pendingDragUpdate.current) {
      onUpdate(element.id, pendingDragUpdate.current);
      pendingDragUpdate.current = null;
    }
  };

  React.useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  const handleDoubleClick = (e: React.MouseEvent) => {
    if (element.type !== 'text') return;
    e.stopPropagation();
    onSelect(e.shiftKey || e.ctrlKey || e.metaKey);
    onInteractionStart();
    setIsEditing(true);
  };

  const handleTextBlur = () => {
    setIsEditing(false);
    if (textRef.current) {
      onUpdate(element.id, {
        content: textRef.current.innerText,
      });
    }
  };

  const handleTextKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsEditing(false);
      if (textRef.current) {
        onUpdate(element.id, {
          content: textRef.current.innerText,
        });
      }
    } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      // Commit edits quickly with Cmd/Ctrl+Enter.
      textRef.current?.blur();
    }
  };

  const handleTextInput = (e: React.FormEvent<HTMLDivElement>) => {
    onUpdateInstant(element.id, { content: e.currentTarget.innerText });
  };

  useEffect(() => {
    if (isEditing && textRef.current) {
      const el = textRef.current;
      if (el.innerText !== element.content) {
        el.innerText = element.content;
      }
      el.focus();
      const selection = window.getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
    } else if (!isEditing && textRef.current) {
      // Sync displayed content when not editing to avoid cursor jumps.
      if (textRef.current.innerText !== element.content) {
        textRef.current.innerText = element.content;
      }
    }
  }, [isEditing, element.content]);

  useEffect(() => {
    // When selection is cleared (e.g., click on blank canvas), exit edit mode.
    setIsEditing(false);
  }, [editingResetKey]);

  const renderContent = () => {
    switch (element.type) {
      case 'text':
        return (
          <div
            ref={textRef}
            contentEditable={isEditing}
            suppressContentEditableWarning
            onBlur={handleTextBlur}
            onKeyDown={handleTextKeyDown}
            onInput={handleTextInput}
            onDoubleClick={handleDoubleClick}
            className="w-full h-full flex items-center justify-center px-2 outline-none"
            style={{
              color: element.styles.color,
              fontSize: `${element.styles.fontSize}px`,
              fontWeight: element.styles.fontWeight,
              cursor: isEditing ? 'text' : 'move',
            }}
          >
            {element.content}
          </div>
        );
      
      case 'image':
        return (
          <img
            src={element.content}
            alt="Canvas element"
            className="w-full h-full object-contain pointer-events-none"
          />
        );
      
      case 'drawing':
        return (
          <img
            src={element.content}
            alt="Drawing"
            className="w-full h-full object-contain pointer-events-none"
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <Resizable
      size={{ width: element.width, height: element.height }}
      onResizeStop={(e, direction, ref, d) => {
        onUpdate(element.id, {
          width: element.width + d.width,
          height: element.height + d.height,
        });
      }}
      onResizeStart={onInteractionStart}
      enable={{
        top: isSelected,
        right: isSelected,
        bottom: isSelected,
        left: isSelected,
        topRight: isSelected,
        bottomRight: isSelected,
        bottomLeft: isSelected,
        topLeft: isSelected,
      }}
      className="absolute"
      style={{
        left: `${element.x}px`,
        top: `${element.y}px`,
        transform: `rotate(${element.styles.rotation || 0}deg)`,
        opacity: element.styles.opacity,
        backgroundColor: element.styles.backgroundColor,
        border: isSelected ? '2px solid #3b82f6' : '1px solid transparent',
        cursor: isDragging ? 'grabbing' : 'grab',
        zIndex: isSelected ? 10 : 1,
      }}
      onMouseDown={handleMouseDown}
    >
      {renderContent()}

      {isSelected && (
        <div className="absolute -top-6 left-0 bg-blue-500 text-white px-2 py-1 rounded text-xs">
          {element.type}
        </div>
      )}
    </Resizable>
  );
}
