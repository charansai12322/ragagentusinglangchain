import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PdfDropzone } from '../features/document-upload/PdfDropzone';
import { PdfUrlForm } from '../features/document-upload/PdfUrlForm';
import { ChatComposer } from '../features/document-chat/ChatComposer';
import { CitationModal } from '../features/document-chat/CitationModal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';

describe('Frontend UI Components', () => {
  describe('PdfDropzone', () => {
    it('renders initial dropzone with instructions', () => {
      render(<PdfDropzone onFileSubmit={vi.fn()} isLoading={false} />);

      expect(screen.getByText(/Choose a PDF or drag it here/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Browse files/i })).toBeInTheDocument();
    });

    it('rejects non-PDF files via error alert', () => {
      render(<PdfDropzone onFileSubmit={vi.fn()} isLoading={false} />);

      const fileInput = document.getElementById('pdf-file-input') as HTMLInputElement;
      const invalidFile = new File(['image bytes'], 'picture.png', { type: 'image/png' });

      fireEvent.change(fileInput, { target: { files: [invalidFile] } });

      expect(screen.getByRole('alert')).toHaveTextContent(/Please select a valid PDF document/i);
    });

    it('displays file details and submit button when valid PDF is selected', () => {
      const onFileSubmit = vi.fn();
      render(<PdfDropzone onFileSubmit={onFileSubmit} isLoading={false} />);

      const fileInput = document.getElementById('pdf-file-input') as HTMLInputElement;
      const validPdf = new File(['%PDF-1.5 test'], 'paper.pdf', { type: 'application/pdf' });

      fireEvent.change(fileInput, { target: { files: [validPdf] } });

      expect(screen.getByText('paper.pdf')).toBeInTheDocument();
      const submitBtn = screen.getByRole('button', { name: /Bring into Room/i });
      expect(submitBtn).toBeInTheDocument();

      fireEvent.click(submitBtn);
      expect(onFileSubmit).toHaveBeenCalledWith(validPdf);
    });
  });

  describe('PdfUrlForm', () => {
    it('validates URL protocol and structure', () => {
      const onUrlSubmit = vi.fn();
      render(<PdfUrlForm onUrlSubmit={onUrlSubmit} isLoading={false} />);

      const input = screen.getByLabelText(/Document Web Address/i);
      const submitBtn = screen.getByRole('button', { name: /Fetch & Ingest/i });

      // Non-http protocol
      fireEvent.change(input, { target: { value: 'ftp://example.com/doc.pdf' } });
      fireEvent.click(submitBtn);

      expect(screen.getByRole('alert')).toHaveTextContent(/Only http:\/\/ and https:\/\/ URLs are supported/i);
      expect(onUrlSubmit).not.toHaveBeenCalled();

      // Valid https URL
      fireEvent.change(input, { target: { value: 'https://example.com/doc.pdf' } });
      fireEvent.click(submitBtn);

      expect(onUrlSubmit).toHaveBeenCalledWith('https://example.com/doc.pdf');
    });
  });

  describe('ChatComposer', () => {
    it('submits on Enter key without shift', () => {
      const onSubmit = vi.fn();
      const onChange = vi.fn();

      render(
        <ChatComposer
          value="What are the conclusions?"
          onChange={onChange}
          onSubmit={onSubmit}
          isLoading={false}
        />
      );

      const textarea = screen.getByRole('textbox', { name: /Ask a question about this document/i });
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

      expect(onSubmit).toHaveBeenCalledTimes(1);
    });

    it('does not submit on Shift+Enter', () => {
      const onSubmit = vi.fn();
      const onChange = vi.fn();

      render(
        <ChatComposer
          value="What are the conclusions?"
          onChange={onChange}
          onSubmit={onSubmit}
          isLoading={false}
        />
      );

      const textarea = screen.getByRole('textbox', { name: /Ask a question about this document/i });
      fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('tracks character length limit counter', () => {
      render(
        <ChatComposer
          value="Hello document"
          onChange={vi.fn()}
          onSubmit={vi.fn()}
          isLoading={false}
        />
      );

      expect(screen.getByText(/14 \/ 2000 chars/i)).toBeInTheDocument();
    });
  });

  describe('CitationModal', () => {
    it('renders citation details, page number, relevance, and excerpt', () => {
      const onClose = vi.fn();
      const citation = {
        page: 7,
        snippet: 'Direct quote from the experimental section.',
        relevance_score: 0.92,
      };

      render(
        <CitationModal
          citation={citation}
          filename="report.pdf"
          onClose={onClose}
        />
      );

      expect(screen.getAllByText(/Page 7/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/92% Match/i)).toBeInTheDocument();
      expect(screen.getByText(/Direct quote from the experimental section./i)).toBeInTheDocument();

      const closeBtn = screen.getByRole('button', { name: /Close citation details/i });
      fireEvent.click(closeBtn);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('renders nothing when citation is null', () => {
      const { container } = render(
        <CitationModal
          citation={null}
          filename="report.pdf"
          onClose={vi.fn()}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('ConfirmDialog', () => {
    it('handles confirm and cancel actions', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          isOpen={true}
          title="Discard Session?"
          message="Confirm deletion."
          confirmLabel="Yes, Discard"
          cancelLabel="No, Keep"
          onConfirm={onConfirm}
          onCancel={onCancel}
        />
      );

      expect(screen.getByText('Discard Session?')).toBeInTheDocument();
      expect(screen.getByText('Confirm deletion.')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: 'No, Keep' }));
      expect(onCancel).toHaveBeenCalledTimes(1);

      fireEvent.click(screen.getByRole('button', { name: 'Yes, Discard' }));
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });
  });
});
