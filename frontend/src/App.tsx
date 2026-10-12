import React, { useState } from 'react';
import { WorkspaceLayout } from './components/layout/WorkspaceLayout';
import { DocumentEntry } from './features/document-upload/DocumentEntry';
import { ChatWorkspace } from './features/document-chat/ChatWorkspace';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { useDocumentSession } from './hooks/useDocumentSession';

export const App: React.FC = () => {
  const {
    session,
    isReady,
    isLoading,
    activeSource,
    error,
    clearError,
    ingestFile,
    ingestUrl,
    deleteSession,
  } = useDocumentSession();

  const [showNewDocConfirm, setShowNewDocConfirm] = useState(false);
  const [isDeletingSession, setIsDeletingSession] = useState(false);

  const handleConfirmNewSession = async () => {
    setIsDeletingSession(true);
    try {
      await deleteSession();
    } finally {
      setIsDeletingSession(false);
      setShowNewDocConfirm(false);
    }
  };

  return (
    <WorkspaceLayout
      hasActiveSession={Boolean(session && isReady)}
      onNewSessionRequest={() => setShowNewDocConfirm(true)}
    >
      {!session || !isReady ? (
        <DocumentEntry
          onFileUpload={ingestFile}
          onUrlUpload={ingestUrl}
          isLoading={isLoading}
          activeSource={activeSource}
          error={error}
          onClearError={clearError}
        />
      ) : (
        <ChatWorkspace
          session={session}
          onResetSession={deleteSession}
        />
      )}

      {/* Global New Session Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showNewDocConfirm}
        title="Start a New Document Session?"
        message="Starting a new session will discard the current document, delete its private in-memory vectors, and clear conversation history."
        confirmLabel="Start New Session"
        cancelLabel="Continue Current"
        variant="primary"
        loading={isDeletingSession}
        onConfirm={handleConfirmNewSession}
        onCancel={() => setShowNewDocConfirm(false)}
      />
    </WorkspaceLayout>
  );
};

export default App;
