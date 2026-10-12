import React, { useEffect, useState } from 'react';
import { BookOpen, RefreshCw, PlusCircle, AlertCircle, CheckCircle2 } from 'lucide-react';
import { BRANDING } from '../../config/branding';
import { apiClient } from '../../services/api';
import { HealthResponse } from '../../types';
import { Button } from '../ui/Button';

export interface AppHeaderProps {
  hasActiveSession: boolean;
  onNewSessionRequest?: () => void;
}

type ConnectionState = 'checking' | 'connected' | 'disconnected';

export const AppHeader: React.FC<AppHeaderProps> = ({
  hasActiveSession,
  onNewSessionRequest,
}) => {
  const [connection, setConnection] = useState<ConnectionState>('checking');
  const [healthInfo, setHealthInfo] = useState<HealthResponse | null>(null);

  const checkHealth = async () => {
    try {
      setConnection('checking');
      const health = await apiClient.getHealth();
      setHealthInfo(health);
      setConnection(health.status === 'healthy' ? 'connected' : 'disconnected');
    } catch {
      setConnection('disconnected');
      setHealthInfo(null);
    }
  };

  useEffect(() => {
    checkHealth();
    // Re-check every 45s
    const interval = setInterval(checkHealth, 45000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      style={{
        backgroundColor: 'var(--color-paper)',
        borderBottom: '1px solid var(--color-sand)',
        padding: '0.875rem 0',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: 'var(--shadow-subtle)',
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
        {/* Brand identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
          <div
            style={{
              width: '2.25rem',
              height: '2.25rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-oat-milk)',
              border: '1px solid var(--color-sand)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-espresso)',
            }}
            aria-hidden="true"
          >
            <BookOpen size={18} />
          </div>
          <div>
            <div
              style={{
                fontFamily: 'var(--font-serif)',
                fontSize: 'var(--text-lg)',
                fontWeight: 600,
                color: 'var(--color-espresso)',
                letterSpacing: '-0.015em',
                lineHeight: 1.2,
              }}
            >
              {BRANDING.productName}
            </div>
            <div
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: 'var(--text-xs)',
                color: 'var(--color-taupe)',
                letterSpacing: '0.01em',
              }}
            >
              {BRANDING.collectionSubtitle}
            </div>
          </div>
        </div>

        {/* Status indicator & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
          {/* Real Backend Status Badge */}
          <div
            className={`badge ${
              connection === 'connected'
                ? 'badge--forest'
                : connection === 'checking'
                ? 'badge--sand'
                : 'badge--terracotta'
            }`}
            title={
              connection === 'connected'
                ? `FastAPI Backend Online • Embedding: ${healthInfo?.embedding_model || 'FastEmbed'} • LLM: ${healthInfo?.groq_model || 'Groq'}`
                : connection === 'checking'
                ? 'Validating backend connection...'
                : 'Backend API unreachable at configured URL'
            }
          >
            {connection === 'connected' ? (
              <CheckCircle2 size={11} aria-hidden="true" />
            ) : connection === 'checking' ? (
              <RefreshCw size={11} className="coffee-spinner--sm" aria-hidden="true" />
            ) : (
              <AlertCircle size={11} aria-hidden="true" />
            )}
            <span>
              {connection === 'connected'
                ? 'Online'
                : connection === 'checking'
                ? 'Connecting…'
                : 'API Offline'}
            </span>
            {connection === 'connected' && healthInfo?.groq_model && (
              <span
                style={{
                  color: 'var(--color-taupe)',
                  marginLeft: '2px',
                  fontWeight: 400,
                }}
              >
                / {healthInfo.groq_model.replace('-versatile', '')}
              </span>
            )}
          </div>

          {/* New Session Action */}
          {hasActiveSession && onNewSessionRequest && (
            <Button
              variant="secondary"
              size="sm"
              icon={<PlusCircle size={14} />}
              onClick={onNewSessionRequest}
            >
              New Document
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};
