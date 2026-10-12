import React from 'react';
import { AppHeader } from './AppHeader';
import { BRANDING } from '../../config/branding';

export interface WorkspaceLayoutProps {
  children: React.ReactNode;
  hasActiveSession: boolean;
  onNewSessionRequest?: () => void;
}

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({
  children,
  hasActiveSession,
  onNewSessionRequest,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: 'var(--color-oat-milk)',
      }}
    >
      <AppHeader
        hasActiveSession={hasActiveSession}
        onNewSessionRequest={onNewSessionRequest}
      />

      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {children}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--color-sand)',
          padding: '1.25rem 0',
          backgroundColor: 'var(--color-oat-milk-subtle)',
          marginTop: 'auto',
        }}
      >
        <div
          className="workspace-container"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            fontSize: 'var(--text-xs)',
            color: 'var(--color-taupe)',
          }}
        >
          <div>
            <span style={{ fontWeight: 500, color: 'var(--color-roasted-cocoa)' }}>
              {BRANDING.productName}
            </span>{' '}
            — Session-isolated in-memory retrieval engine.
          </div>
          <div style={{ display: 'flex', gap: '1.25rem' }}>
            <span>Private In-Memory Vectors</span>
            <span>FastEmbed Local Embeddings</span>
            <span>Grounded Page Citations</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
