import React from 'react';
import { FileText, Layers, BookOpen, Trash2 } from 'lucide-react';
import { IconButton } from '../../components/ui/IconButton';

export interface DocumentContextBarProps {
  filename: string;
  totalPages: number;
  chunkCount: number;
  status: string;
  onResetRequest: () => void;
}

export const DocumentContextBar: React.FC<DocumentContextBarProps> = ({
  filename,
  totalPages,
  chunkCount,
  status,
  onResetRequest,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-paper)',
        borderBottom: '1px solid var(--color-sand)',
        padding: '0.75rem 0',
      }}
    >
      <div
        className="workspace-container"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        {/* Document identity & stats */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            minWidth: 0,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minWidth: 0,
            }}
          >
            <FileText
              size={18}
              style={{ color: 'var(--color-caramel-hover)', flexShrink: 0 }}
              aria-hidden="true"
            />
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontWeight: 600,
                fontSize: 'var(--text-sm)',
                color: 'var(--color-espresso)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: '320px',
              }}
              title={filename}
            >
              {filename}
            </span>
          </div>

          {/* Metadata badges */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flexWrap: 'wrap',
            }}
          >
            {totalPages > 0 && (
              <span className="badge badge--sand">
                <BookOpen size={11} aria-hidden="true" />
                <span>{totalPages} {totalPages === 1 ? 'page' : 'pages'}</span>
              </span>
            )}
            {chunkCount > 0 && (
              <span className="badge badge--sand">
                <Layers size={11} aria-hidden="true" />
                <span>{chunkCount} chunks</span>
              </span>
            )}
            <span className="badge badge--forest">
              <span className="status-dot status-dot--ready" aria-hidden="true" />
              <span>{status === 'ready' ? 'Ready' : status}</span>
            </span>
          </div>
        </div>

        {/* Close/Remove document action */}
        <div>
          <IconButton
            icon={<Trash2 size={16} />}
            ariaLabel="Close document and clear session"
            variant="ghost"
            onClick={onResetRequest}
          />
        </div>
      </div>
    </div>
  );
};
