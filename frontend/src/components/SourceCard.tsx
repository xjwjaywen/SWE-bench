import type { MessageSource } from '../types';

const FILE_ICONS: Record<string, string> = {
  pdf: '📄', docx: '📝', xlsx: '📊', pptx: '📊',
  csv: '📊', txt: '📃', png: '🖼️', jpg: '🖼️',
  zip: '📦',
};

function getIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return FILE_ICONS[ext] || '📎';
}

interface Props {
  source: MessageSource;
}

export function SourceCard({ source }: Props) {
  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-gray-50 text-sm">
      <div className="font-medium text-gray-800 mb-1">{source.subject}</div>
      <div className="text-gray-500 text-xs space-y-0.5">
        <div>From: {source.from_} {source.from_email ? `<${source.from_email}>` : ''}</div>
        <div>Date: {source.date}</div>
      </div>
      {source.attachments.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {source.attachments.map((att, i) => (
            <a
              key={i}
              href={`/api/attachments/${att}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-white border border-gray-200 rounded text-xs text-blue-600 hover:bg-blue-50"
            >
              <span>{getIcon(att)}</span>
              <span className="truncate max-w-[120px]">{att}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
