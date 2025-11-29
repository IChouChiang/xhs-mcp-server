import React from 'react';
import { 
  AlignLeft, 
  AlignCenter, 
  AlignRight, 
  AlignVerticalJustifyStart,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignHorizontalDistributeCenter,
  AlignVerticalDistributeCenter
} from 'lucide-react';

interface AlignmentMenuProps {
  selectedCount: number;
  onAlign: (alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => void;
  onDistribute: (direction: 'horizontal' | 'vertical') => void;
}

export default function AlignmentMenu({ selectedCount, onAlign, onDistribute }: AlignmentMenuProps) {
  if (selectedCount < 2) return null;

  return (
    <div className="flex items-center gap-1 border-l border-gray-200 pl-4 ml-2">
      <span className="text-gray-600 text-sm mr-2">{selectedCount} selected</span>
      
      {/* Horizontal Alignment */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          onClick={() => onAlign('left')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Left"
        >
          <AlignLeft className="w-4 h-4 text-gray-700" />
        </button>
        <button
          onClick={() => onAlign('center')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Center"
        >
          <AlignCenter className="w-4 h-4 text-gray-700" />
        </button>
        <button
          onClick={() => onAlign('right')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Right"
        >
          <AlignRight className="w-4 h-4 text-gray-700" />
        </button>
      </div>

      {/* Vertical Alignment */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          onClick={() => onAlign('top')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Top"
        >
          <AlignVerticalJustifyStart className="w-4 h-4 text-gray-700" />
        </button>
        <button
          onClick={() => onAlign('middle')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Middle"
        >
          <AlignVerticalJustifyCenter className="w-4 h-4 text-gray-700" />
        </button>
        <button
          onClick={() => onAlign('bottom')}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
          title="Align Bottom"
        >
          <AlignVerticalJustifyEnd className="w-4 h-4 text-gray-700" />
        </button>
      </div>

      {/* Distribution */}
      {selectedCount >= 3 && (
        <div className="flex items-center gap-1">
          <button
            onClick={() => onDistribute('horizontal')}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title="Distribute Horizontally"
          >
            <AlignHorizontalDistributeCenter className="w-4 h-4 text-gray-700" />
          </button>
          <button
            onClick={() => onDistribute('vertical')}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            title="Distribute Vertically"
          >
            <AlignVerticalDistributeCenter className="w-4 h-4 text-gray-700" />
          </button>
        </div>
      )}
    </div>
  );
}
