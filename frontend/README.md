# The Reading Room — Editorial RAG Workspace Frontend

A production-grade, editorial document-intelligence interface built with **React**, **Vite**, and **TypeScript**. Inspired by independent book publishers, specialty coffee packaging, and carefully typeset research journals.

Designed to make one core workflow effortless:
**Bring a PDF into the workspace, ask meaningful questions about its contents, and trace answers back to original pages with verbatim evidence citations.**

---

## 1. Design Identity & Token System

### Visual Concept: The Reading Room
- **Editorial rather than corporate:** Warm, calm, tactile, paper-like reading surfaces.
- **Content-first:** Conversations occupy generous whitespace with rich typography rather than cramped dashboard widgets.
- **Zero generic AI slop:** No meaningless robot mascots, fake usage meters, or simulated progress bars.

### Palette Foundation: Espresso, Parchment & Caramel
| Token | Color | Semantic Role |
| :--- | :--- | :--- |
| `Espresso` | `#35231E` | Primary typography, headers, emphasized controls |
| `Dark Roast` | `#241713` | Deepest accents and pressed interactive states |
| `Roasted Cocoa`| `#65483B` | Secondary text, subtle borders, metadata labels |
| `Coffee Bean` | `#80624F` | Muted labels, icon accents |
| `Caramel` | `#B9875B` | Active highlights, focus rings, selected tabs |
| `Oat Milk` | `#F5EFE5` | Main warm ambient background |
| `Paper` | `#FFFCF7` | Reading surface for messages and cards |
| `Sand` | `#E8DCCB` | Tactile surface borders, divider rules |
| `Taupe` | `#857365` | Accessible secondary metadata (contrast-verified) |
| `Forest Green`| `#42644C` | Ready states and verified online indicators |
| `Burnt Terracotta`| `#A84F3D` | Errors, security rejections, destructive dialogs |

### Typographic Hierarchy
- **Headings & Display:** `DM Serif Display`, serif
- **Body & Interface:** `DM Sans`, sans-serif
- **Metadata & Technical:** `IBM Plex Mono`, monospace

---

## 2. Component Architecture

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppHeader.tsx            # Live backend health pill, brand identity, new session trigger
│   │   └── WorkspaceLayout.tsx      # Responsive header, reading canvas, editorial footer
│   └── ui/
│       ├── Button.tsx               # Primary, Secondary, Ghost, Danger button with forwardRef
│       ├── IconButton.tsx           # Accessible icon button with tooltips
│       ├── Spinner.tsx              # Tactile coffee-ring indeterminate spinner
│       ├── InlineNotice.tsx         # Structured alert & error notice with action buttons
│       └── ConfirmDialog.tsx        # Accessible modal dialog with focus management
├── features/
│   ├── document-upload/
│   │   ├── DocumentEntry.tsx        # Tabbed container (File Upload vs Remote URL)
│   │   ├── PdfDropzone.tsx          # Drag-and-drop zone, file selector, size validation
│   │   ├── PdfUrlForm.tsx           # URL input with scheme & syntax validation
│   │   └── IngestionProgress.tsx    # Truthful indeterminate ingestion indicator
│   └── document-chat/
│       ├── ChatWorkspace.tsx        # Coordinates conversation, composer, and citations
│       ├── DocumentContextBar.tsx   # Filename, page count, chunk count, status
│       ├── ConversationList.tsx     # Message stream with editorial question starters
│       ├── MessageItem.tsx          # Multi-turn turns, formatting, clickable citations
│       ├── CitationPill.tsx         # Compact page reference chip
│       ├── CitationModal.tsx        # Verbatim excerpt modal with cosine score
│       └── ChatComposer.tsx         # Multiline textarea (1-2000 chars, Enter-to-ask)
├── hooks/
│   ├── useDocumentSession.ts        # Ingest file/URL, session status, session deletion
│   └── useDocumentChat.ts           # Multi-turn message state, citations, retry preservation
├── config/
│   └── branding.ts                  # Centralized product constants and suggested inquiries
├── lib/
│   └── errors.ts                    # User-friendly API error mapping and recovery guidance
├── services/
│   └── api.ts                       # Typed API client with AbortSignal, FormData, errors
├── styles/
│   ├── tokens.css                   # Custom property design tokens
│   ├── global.css                   # Resets, tactile scrollbars, selection styles
│   ├── components.css               # Buttons, badges, dialogs, spinners
│   └── index.css                    # Master bundle stylesheet
├── types/
│   └── index.ts                     # TypeScript models mirroring backend Pydantic schemas
├── App.tsx                          # Root application orchestrator
└── main.tsx                         # Entry point
```

---

## 3. Environment Configuration

Create a `.env` file from `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

| Variable | Local Default | Production (Vercel) | Purpose |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | `https://your-render-backend.onrender.com` | Base URL of the FastAPI backend |

> **Security Note:** The browser application never receives, stores, or handles `GROQ_API_KEY`. LLM inference is strictly proxied through the backend.

---

## 4. Local Development & Verification

### Install Dependencies
```bash
npm install
```

### Type Checking
```bash
npm run typecheck
```

### Run Unit & Component Tests (Vitest)
```bash
npm test
```

### Build Production Bundle
```bash
npm run build
```

### Start Vite Development Server
```bash
npm run dev
```

---

## 5. Live Backend Integration
The frontend seamlessly communicates with the FastAPI service endpoints:
- `GET /api/health` — Real health check badge with active LLM and embedding info.
- `POST /api/documents/upload` — Direct multipart PDF ingestion (up to 15MB).
- `POST /api/documents/url` — Protected remote PDF ingestion.
- `GET /api/documents/{session_id}/status` — Live session status polling.
- `POST /api/documents/{session_id}/chat` — Grounded multi-turn QA with page citations.
- `DELETE /api/documents/{session_id}` — Session teardown and vector index deletion.
