import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import Toolbar from './components/Toolbar';
import Canvas from './components/Canvas';
import AIDialog from './components/AIDialog';
import PublishModal from './components/PublishModal';

export interface CanvasElement {
  id: string;
  type: 'text' | 'image' | 'drawing';
  x: number;
  y: number;
  width: number;
  height: number;
  content: any;
  styles: {
    fontSize?: number;
    fontWeight?: string;
    color?: string;
    backgroundColor?: string;
    opacity?: number;
    rotation?: number;
  };
}

export type AssistantMessage = { role: 'user' | 'assistant'; content: string };

export default function App() {
  const [elements, setElements] = useState<CanvasElement[]>([]);
  const [selectedElementIds, setSelectedElementIds] = useState<string[]>([]);
  const [canvasViewport, setCanvasViewport] = useState({ centerX: 0, centerY: 0 });
  const [editingResetKey, setEditingResetKey] = useState(0);
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const [showAssistant, setShowAssistant] = useState(true);
  const [aiMessages, setAiMessages] = useState<AssistantMessage[]>([
    {
      role: 'assistant',
      content:
        'Hi! Select elements and tell me how you want to modify them. Try commands like "make it bigger", "change color to red", "align left", or "distribute horizontally".',
    },
  ]);
  const [history, setHistory] = useState<CanvasElement[][]>([]);
  const [redoStack, setRedoStack] = useState<CanvasElement[][]>([]);
  const [isUndoRedoHotkeyEnabled] = useState(true);
  const [publishPlatform, setPublishPlatform] = useState<'x' | 'xiaohongshu' | 'douyin'>('x');
  const [showPublishModal, setShowPublishModal] = useState(false);
  const interactionSnapshot = useRef<CanvasElement[] | null>(null);

  const selectedElements = useMemo(
    () => elements.filter(el => selectedElementIds.includes(el.id)),
    [elements, selectedElementIds]
  );

  const deepCopyElements = (list: CanvasElement[]) =>
    list.map(el => ({
      ...el,
      styles: { ...el.styles },
    }));

  const recordAndSet = (updater: (prev: CanvasElement[]) => CanvasElement[]) => {
    setElements(prev => {
      const next = updater(prev);
      if (next === prev) return prev;
      const baseline = interactionSnapshot.current ?? prev;
      setHistory(h => [...h.slice(-19), deepCopyElements(baseline)]);
      setRedoStack([]);
      interactionSnapshot.current = null;
      return next;
    });
  };

  const setElementsInstant = (updater: (prev: CanvasElement[]) => CanvasElement[]) => {
    setElements(prev => {
      const next = updater(prev);
      return next;
    });
  };

  const snapshotState = () => {
    interactionSnapshot.current = deepCopyElements(elements);
  };

  const undo = useCallback(() => {
    setHistory(prevHistory => {
      if (!prevHistory.length) return prevHistory;
      const last = prevHistory[prevHistory.length - 1];
      setRedoStack(r => [elements, ...r]);
      setElements(last);
      setSelectedElementIds([]);
      setEditingResetKey(v => v + 1);
      return prevHistory.slice(0, -1);
    });
  }, [elements]);

  const redo = useCallback(() => {
    setRedoStack(prevRedo => {
      if (!prevRedo.length) return prevRedo;
      const [first, ...rest] = prevRedo;
      setHistory(h => [...h, elements]);
      setElements(first);
      setSelectedElementIds([]);
      setEditingResetKey(v => v + 1);
      return rest;
    });
  }, [elements]);

  useEffect(() => {
    if (!isUndoRedoHotkeyEnabled) return;
    const onKeyDown = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;
      if (!meta) return;
      if (e.key.toLowerCase() === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      } else if ((e.key.toLowerCase() === 'y') || (e.key.toLowerCase() === 'z' && e.shiftKey)) {
        e.preventDefault();
        redo();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [undo, redo, isUndoRedoHotkeyEnabled]);

  const addElement = (type: 'text' | 'image' | 'drawing', content: any) => {
    const width = type === 'text' ? 200 : type === 'image' ? 300 : 400;
    const height = type === 'text' ? 50 : type === 'image' ? 300 : 300;

    const newElement: CanvasElement = {
      id: `${type}-${Date.now()}`,
      type,
      x: canvasViewport.centerX - width / 2,
      y: canvasViewport.centerY - height / 2,
      width,
      height,
      content,
      styles: {
        fontSize: 16,
        fontWeight: 'normal',
        color: '#000000',
        backgroundColor: type === 'text' ? 'transparent' : '#ffffff',
        opacity: 1,
        rotation: 0,
      },
    };
    recordAndSet(prev => [...prev, newElement]);
    setSelectedElementIds([newElement.id]);
  };

  const updateElement = (id: string, updates: Partial<CanvasElement>) => {
    recordAndSet(prev =>
      prev.map(el => (el.id === id ? { ...el, ...updates } : el))
    );
  };

  const updateElementInstant = (id: string, updates: Partial<CanvasElement>) => {
    setElementsInstant(prev =>
      prev.map(el => (el.id === id ? { ...el, ...updates } : el))
    );
  };

  const updateElementStyles = (id: string, styles: Partial<CanvasElement['styles']>) => {
    recordAndSet(prev =>
      prev.map(el => (el.id === id ? { ...el, styles: { ...el.styles, ...styles } } : el))
    );
  };

  const deleteElement = (id: string) => {
    recordAndSet(prev => prev.filter(el => el.id !== id));
    setSelectedElementIds(selectedElementIds.filter(sid => sid !== id));
  };

  const deleteSelected = () => {
    recordAndSet(prev => prev.filter(el => !selectedElementIds.includes(el.id)));
    setSelectedElementIds([]);
  };

  const layerAction = (action: 'bringToFront' | 'sendToBack') => {
    if (selectedElementIds.length === 0) return;

    setElements(prev => {
      const selected = prev.filter(el => selectedElementIds.includes(el.id));
      const others = prev.filter(el => !selectedElementIds.includes(el.id));
      return action === 'bringToFront' ? [...others, ...selected] : [...selected, ...others];
    });
  };

  const toggleElementSelection = (id: string, isMultiSelect: boolean) => {
    if (isMultiSelect) {
      if (selectedElementIds.includes(id)) {
        setSelectedElementIds(selectedElementIds.filter(sid => sid !== id));
      } else {
        setSelectedElementIds([...selectedElementIds, id]);
      }
    } else {
      setSelectedElementIds([id]);
    }
  };

  const clearSelection = () => {
    setSelectedElementIds([]);
    setEditingResetKey((v) => v + 1);
  };

  const alignElements = (alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => {
    if (selectedElements.length < 2) return;

    const positions = selectedElements.map(el => ({
      id: el.id,
      left: el.x,
      right: el.x + el.width,
      top: el.y,
      bottom: el.y + el.height,
      centerX: el.x + el.width / 2,
      centerY: el.y + el.height / 2,
    }));

    let updates: { [key: string]: Partial<CanvasElement> } = {};

    switch (alignment) {
      case 'left':
        const minLeft = Math.min(...positions.map(p => p.left));
        positions.forEach(p => {
          updates[p.id] = { x: minLeft };
        });
        break;
      case 'center':
        const avgCenterX = positions.reduce((sum, p) => sum + p.centerX, 0) / positions.length;
        positions.forEach((p, i) => {
          updates[p.id] = { x: avgCenterX - selectedElements[i].width / 2 };
        });
        break;
      case 'right':
        const maxRight = Math.max(...positions.map(p => p.right));
        positions.forEach((p, i) => {
          updates[p.id] = { x: maxRight - selectedElements[i].width };
        });
        break;
      case 'top':
        const minTop = Math.min(...positions.map(p => p.top));
        positions.forEach(p => {
          updates[p.id] = { y: minTop };
        });
        break;
      case 'middle':
        const avgCenterY = positions.reduce((sum, p) => sum + p.centerY, 0) / positions.length;
        positions.forEach((p, i) => {
          updates[p.id] = { y: avgCenterY - selectedElements[i].height / 2 };
        });
        break;
      case 'bottom':
        const maxBottom = Math.max(...positions.map(p => p.bottom));
        positions.forEach((p, i) => {
          updates[p.id] = { y: maxBottom - selectedElements[i].height };
        });
        break;
    }

    recordAndSet(prev =>
      prev.map(el => (updates[el.id] ? { ...el, ...updates[el.id] } : el))
    );
  };

  const distributeElements = (direction: 'horizontal' | 'vertical') => {
    if (selectedElements.length < 3) return;

    const sorted = [...selectedElements].sort((a, b) =>
      direction === 'horizontal' ? a.x - b.x : a.y - b.y
    );

    const first = sorted[0];
    const last = sorted[sorted.length - 1];

    if (direction === 'horizontal') {
      const totalSpace = (last.x + last.width) - first.x;
      const totalWidth = sorted.reduce((sum, el) => sum + el.width, 0);
      const gap = (totalSpace - totalWidth) / (sorted.length - 1);

      let currentX = first.x;
      sorted.forEach(el => {
        updateElement(el.id, { x: currentX });
        currentX += el.width + gap;
      });
    } else {
      const totalSpace = (last.y + last.height) - first.y;
      const totalHeight = sorted.reduce((sum, el) => sum + el.height, 0);
      const gap = (totalSpace - totalHeight) / (sorted.length - 1);

      let currentY = first.y;
      sorted.forEach(el => {
        updateElement(el.id, { y: currentY });
        currentY += el.height + gap;
      });
    }
  };

  const handleAIModify = async (prompt: string, targets: CanvasElement[] = selectedElements) => {
    if (targets.length === 0) return;

    // Send payload to placeholder AI API (server logs it).
    try {
      const res = await fetch('/api/ai/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, elements: targets }),
      });
      
      const data = await res.json();
      if (data.message && data.message !== "AI is offline, using local logic.") {
         setAiMessages(prev => [
           ...prev, 
           { role: 'assistant', content: data.message }
         ]);
      }

    } catch (err) {
      console.error('AI apply error', err);
    }

    // Mock AI modifications based on prompt keywords
    const lowerPrompt = prompt.toLowerCase();

    targets.forEach(selectedElement => {
      if (lowerPrompt.includes('bigger') || lowerPrompt.includes('larger')) {
        updateElement(selectedElement.id, {
          width: selectedElement.width * 1.3,
          height: selectedElement.height * 1.3,
        });
      } else if (lowerPrompt.includes('smaller')) {
        updateElement(selectedElement.id, {
          width: selectedElement.width * 0.7,
          height: selectedElement.height * 0.7,
        });
      } else if (lowerPrompt.includes('red')) {
        updateElementStyles(selectedElement.id, { color: '#ef4444' });
      } else if (lowerPrompt.includes('blue')) {
        updateElementStyles(selectedElement.id, { color: '#3b82f6' });
      } else if (lowerPrompt.includes('green')) {
        updateElementStyles(selectedElement.id, { color: '#10b981' });
      } else if (lowerPrompt.includes('bold')) {
        updateElementStyles(selectedElement.id, { fontWeight: 'bold' });
      } else if (lowerPrompt.includes('rotate')) {
        const currentRotation = selectedElement.styles.rotation || 0;
        updateElementStyles(selectedElement.id, { rotation: currentRotation + 45 });
      }
    });

    if (lowerPrompt.includes('align left')) {
      alignElements('left');
    } else if (lowerPrompt.includes('align right')) {
      alignElements('right');
    } else if (lowerPrompt.includes('align top')) {
      alignElements('top');
    } else if (lowerPrompt.includes('align bottom')) {
      alignElements('bottom');
    } else if (lowerPrompt.includes('center horizontally')) {
      alignElements('center');
    } else if (lowerPrompt.includes('center vertically')) {
      alignElements('middle');
    } else if (lowerPrompt.includes('distribute horizontally')) {
      distributeElements('horizontal');
    } else if (lowerPrompt.includes('distribute vertically')) {
      distributeElements('vertical');
    }
  };

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (selectedElements.length === 0) {
        setAiSuggestions([]);
        return;
      }
      try {
        const res = await fetch('/api/ai/suggestions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ elements: selectedElements }),
        });
        const data = await res.json();
        setAiSuggestions((data?.suggestions as string[]) ?? []);
      } catch (err) {
        console.error('AI suggestion error', err);
        setAiSuggestions([]);
      }
    };
    fetchSuggestions();
  }, [selectedElements]);

  const handlePublish = async (platform: 'x' | 'xiaohongshu' | 'douyin') => {
    if (elements.length === 0) return;
    try {
      await fetch('/api/ai/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ elements, platform }),
      });
    } catch (err) {
      console.error('AI publish error', err);
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex flex-col h-screen bg-gray-50">
        {/* Top Toolbar */}
        <Toolbar
          onAddElement={addElement}
          selectedElementsCount={selectedElements.length}
          totalElementsCount={elements.length}
          onAlign={alignElements}
          onDistribute={distributeElements}
          onDeleteSelected={deleteSelected}
          onLayerAction={layerAction}
          onPublish={() => setShowPublishModal(true)}
          onUndo={undo}
          onRedo={redo}
          canUndo={history.length > 0}
          canRedo={redoStack.length > 0}
        />

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Canvas */}
          <div className="relative flex-1 flex flex-col overflow-hidden">
            <Canvas
              elements={elements}
              selectedElementIds={selectedElementIds}
              onSelectElement={toggleElementSelection}
              onClearSelection={clearSelection}
              onUpdateElement={updateElement}
              onUpdateElementInstant={updateElementInstant}
              onInteractionStart={snapshotState}
              onViewportChange={setCanvasViewport}
              editingResetKey={editingResetKey}
            />

            {!showAssistant && (
              <button
                onClick={() => setShowAssistant(true)}
                className="absolute top-16 right-4 z-30 flex items-center justify-center rounded-full bg-white/90 p-3 text-emerald-600 shadow-md border border-emerald-100 hover:bg-emerald-50 transition"
                aria-label="Open AI Assistant"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 10h8m-8 4h5m7 0v4l-3-3H7a3 3 0 01-3-3V7a3 3 0 013-3h10a3 3 0 013 3v7z" />
                </svg>
              </button>
            )}
          </div>

          {/* AI Dialog Sidebar */}
          <div
            className={`flex h-full flex-col border-l border-slate-200 bg-white transition-all duration-300 ease-in-out ${
              showAssistant ? 'w-[360px] translate-x-0 opacity-100' : 'w-0 translate-x-4 opacity-0'
            }`}
          >
            {showAssistant && (
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 bg-gradient-to-r from-emerald-500/10 to-lime-400/10">
                  <div className="text-sm font-semibold text-slate-900">AI Assistant</div>
                  <button
                    onClick={() => setShowAssistant(false)}
                    className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Collapse
                  </button>
                </div>
                <div className="flex-1 overflow-hidden">
                  <AIDialog
                    selectedElements={selectedElements}
                    suggestions={aiSuggestions}
                    messages={aiMessages}
                    onMessagesChange={setAiMessages}
                    onSubmit={(prompt) => handleAIModify(prompt, selectedElements)}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <PublishModal
        open={showPublishModal}
        platform={publishPlatform}
        onPlatformChange={setPublishPlatform}
        onConfirm={() => {
          handlePublish(publishPlatform);
          setShowPublishModal(false);
        }}
        onClose={() => setShowPublishModal(false)}
        disabled={elements.length === 0}
      />
    </DndProvider>
  );
}
