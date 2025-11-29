import React from 'react';

type Platform = 'x' | 'xiaohongshu' | 'douyin';

interface PublishModalProps {
  open: boolean;
  platform: Platform;
  onPlatformChange: (platform: Platform) => void;
  onConfirm: () => void;
  onClose: () => void;
  disabled?: boolean;
}

export default function PublishModal({
  open,
  platform,
  onPlatformChange,
  onConfirm,
  onClose,
  disabled,
}: PublishModalProps) {
  if (!open) return null;

  const options: { label: string; value: Platform }[] = [
    { label: 'X (Twitter)', value: 'x' },
    { label: 'Xiaohongshu', value: 'xiaohongshu' },
    { label: 'Douyin', value: 'douyin' },
  ];

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="w-[320px] rounded-2xl bg-white p-4 shadow-xl border border-slate-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-slate-900">Select Platform</h3>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700 rounded-md px-2 py-1 text-sm"
          >
            Close
          </button>
        </div>
        <div className="space-y-2">
          {options.map(opt => (
            <label
              key={opt.value}
              className={`flex items-center gap-2 rounded-xl border px-3 py-2 cursor-pointer transition ${
                platform === opt.value
                  ? 'border-emerald-400 bg-emerald-50 text-emerald-700'
                  : 'border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <input
                type="radio"
                name="platform"
                value={opt.value}
                checked={platform === opt.value}
                onChange={() => onPlatformChange(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={disabled}
            className="px-4 py-2 rounded-xl bg-emerald-500 text-white hover:bg-emerald-600 disabled:bg-slate-300 disabled:text-slate-600 disabled:cursor-not-allowed shadow"
          >
            Publish
          </button>
        </div>
      </div>
    </div>
  );
}
