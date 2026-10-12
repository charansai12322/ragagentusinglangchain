import React, { useState } from 'react';
import { DocumentContextBar } from './DocumentContextBar';
import { ConversationList } from './ConversationList';
import { ChatComposer } from './ChatComposer';
import { CitationModal } from './CitationModal';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { useDocumentChat } from '../../hooks/useDocumentChat';
import { formatApiError } from '../../lib/errors';
import { DocumentIngestResponse } from '../../types';

export interface ChatWorkspaceProps {
  session: DocumentIngestResponse;
  onResetSession: () => Promise<void>;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  session,
  onResetSession,
}) => {
  const [showConfirmReset, setShowConfirmReset] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const {
    messages,
    input,
    setInput,
    isAsking,
    error: chatError,
    clearChatError,
    activeCitation,
    inspectCitation,
    closeCitation,
    askQuestion,
  } = useDocumentChat(session.session_id, () => {
    // Session expired callback
  });

  const handleConfirmReset = async () => {
    setIsResetting(true);
    try {
      await onResetSession();
    } finally {
      setIsResetting(false);
      setShowConfirmReset(false);
    }
  };

  const formattedError = chatError ? formatApiError(chatError) : null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Context metadata strip */}
      <DocumentContextBar
        filename={session.filename}
        totalPages={session.total_pages}
        chunkCount={session.chunk_count}
        status={session.status}
        onResetRequest={() => setShowConfirmReset(true)}
      />

      {/* Floating or Inline Chat Error Notice */}
      {formattedError && (
        <div className="workspace-container" style={{ marginTop: '1rem' }}>
          <InlineNotice
            variant="error"
            title={formattedError.title}
            message={`${formattedError.detail} ${
              formattedError.recovery ? `Advice: ${formattedError.recovery}` : ''
            }`}
            onDismiss={clearChatError}
            action={
              input
                ? {
                    label: 'Retry question',
                    onClick: () => {
                      clearChatError();
                      askQuestion();
                    },
                  }
                : undefined
            }
          />
        </div>
      )}

      {/* Scrollable Conversation Feed */}
      <ConversationList
        messages={messages}
        filename={session.filename}
        onCitationClick={inspectCitation}
        onSelectSuggestedQuestion={(q) => {
          askQuestion(q);
        }}
      />

      {/* Bottom Sticky Multiline Chat Composer */}
      <ChatComposer
        value={input}
        onChange={setInput}
        onSubmit={() => askQuestion()}
        isLoading={isAsking}
        disabled={isResetting}
      />

      {/* Citation Inspector Modal */}
      <CitationModal
        citation={activeCitation}
        filename={session.filename}
        onClose={closeCitation}
      />

      {/* Confirm Session Removal Dialog */}
      <ConfirmDialog
        isOpen={showConfirmReset}
        title="Leave Document Session?"
        message={`Are you sure you want to close "${session.filename}"? This will delete the in-memory vector index and clear your current conversation.`}
        confirmLabel="Close Session"
        cancelLabel="Keep Reading"
        variant="danger"
        loading={isResetting}
        onConfirm={handleConfirmReset}
        onCancel={() => setShowConfirmReset(false)}
      />
    </div>
  );
};
