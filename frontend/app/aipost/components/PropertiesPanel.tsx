import React from 'react';
import { Trash2, Palette, Type as TypeIcon, Maximize, Layers } from 'lucide-react';
import { CanvasElement } from '../App';

interface PropertiesPanelProps {
  selectedElements: CanvasElement[];
  onUpdate: (id: string, updates: Partial<CanvasElement>) => void;
  onUpdateStyles: (id: string, styles: Partial<CanvasElement['styles']>) => void;
  onDelete: (id: string) => void;
}

export default function PropertiesPanel({
  selectedElements,
  onUpdate,
  onUpdateStyles,
  onDelete,
}: PropertiesPanelProps) {
  if (selectedElements.length === 0) {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <div className="text-gray-500 text-center mt-8">
          Select an element to edit its properties
        </div>
      </div>
    );
  }

  if (selectedElements.length > 1) {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-gray-700" />
            <h2 className="text-gray-900">Multiple Selected</h2>
          </div>
        </div>
        <div className="space-y-3">
          <div className="bg-blue-50 px-3 py-2 rounded-lg">
            <span className="text-blue-700">{selectedElements.length} elements selected</span>
          </div>
          <div className="text-gray-600 text-sm">
            <p className="mb-2">Selected elements:</p>
            <ul className="space-y-1">
              {selectedElements.map(el => (
                <li key={el.id} className="flex items-center justify-between">
                  <span className="capitalize">{el.type}</span>
                  <button
                    onClick={() => onDelete(el.id)}
                    className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="pt-4 border-t border-gray-200 text-sm text-gray-500">
            Use the alignment tools in the toolbar or ask AI to modify all selected elements
          </div>
        </div>
      </div>
    );
  }

  const selectedElement = selectedElements[0];

  return (
    <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-gray-900">Properties</h2>
        <button
          onClick={() => onDelete(selectedElement.id)}
          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          title="Delete element"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        {/* Type Badge */}
        <div className="bg-gray-100 px-3 py-2 rounded-lg">
          <span className="text-gray-700 capitalize">{selectedElement.type}</span>
        </div>

        {/* Text Content */}
        {selectedElement.type === 'text' && (
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-gray-700">
              <TypeIcon className="w-4 h-4" />
              Text Content
            </label>
            <textarea
              value={selectedElement.content}
              onChange={(e) =>
                onUpdate(selectedElement.id, {
                  content: e.target.value,
                })
              }
              className="w-full min-h-[120px] px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Color */}
        {selectedElement.type === 'text' && (
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-gray-700">
              <Palette className="w-4 h-4" />
              Text Color
            </label>
            <input
              type="color"
              value={selectedElement.styles.color}
              onChange={(e) =>
                onUpdateStyles(selectedElement.id, { color: e.target.value })
              }
              className="w-full h-10 rounded cursor-pointer"
            />
          </div>
        )}

        {/* Font Size */}
        {selectedElement.type === 'text' && (
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-gray-700">
              <TypeIcon className="w-4 h-4" />
              Font Size
            </label>
            <input
              type="range"
              min="8"
              max="72"
              value={selectedElement.styles.fontSize}
              onChange={(e) =>
                onUpdateStyles(selectedElement.id, {
                  fontSize: Number(e.target.value),
                })
              }
              className="w-full"
            />
            <div className="text-gray-600">{selectedElement.styles.fontSize}px</div>
          </div>
        )}

        {/* Font Weight */}
        {selectedElement.type === 'text' && (
          <div className="space-y-2">
            <label className="text-gray-700">Font Weight</label>
            <select
              value={selectedElement.styles.fontWeight}
              onChange={(e) =>
                onUpdateStyles(selectedElement.id, {
                  fontWeight: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="normal">Normal</option>
              <option value="bold">Bold</option>
              <option value="lighter">Light</option>
            </select>
          </div>
        )}

        {/* Background Color */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-gray-700">
            <Palette className="w-4 h-4" />
            Background
          </label>
          <input
            type="color"
            value={selectedElement.styles.backgroundColor}
            onChange={(e) =>
              onUpdateStyles(selectedElement.id, {
                backgroundColor: e.target.value,
              })
            }
            className="w-full h-10 rounded cursor-pointer"
          />
          <button
            onClick={() =>
              onUpdateStyles(selectedElement.id, {
                backgroundColor: 'transparent',
              })
            }
            className="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Transparent
          </button>
        </div>

        {/* Opacity */}
        <div className="space-y-2">
          <label className="text-gray-700">Opacity</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={selectedElement.styles.opacity}
            onChange={(e) =>
              onUpdateStyles(selectedElement.id, {
                opacity: Number(e.target.value),
              })
            }
            className="w-full"
          />
          <div className="text-gray-600">
            {Math.round((selectedElement.styles.opacity || 1) * 100)}%
          </div>
        </div>

        {/* Rotation */}
        <div className="space-y-2">
          <label className="text-gray-700">Rotation</label>
          <input
            type="range"
            min="0"
            max="360"
            value={selectedElement.styles.rotation}
            onChange={(e) =>
              onUpdateStyles(selectedElement.id, {
                rotation: Number(e.target.value),
              })
            }
            className="w-full"
          />
          <div className="text-gray-600">{selectedElement.styles.rotation}°</div>
        </div>

        {/* Position & Size */}
        <div className="space-y-2 pt-4 border-t border-gray-200">
          <label className="flex items-center gap-2 text-gray-700">
            <Maximize className="w-4 h-4" />
            Dimensions
          </label>
          <div className="grid grid-cols-2 gap-2 text-gray-600">
            <div>
              <div>X: {Math.round(selectedElement.x)}px</div>
              <div>Y: {Math.round(selectedElement.y)}px</div>
            </div>
            <div>
              <div>W: {Math.round(selectedElement.width)}px</div>
              <div>H: {Math.round(selectedElement.height)}px</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
