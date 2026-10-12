/**
 * Centralized branding and product identity constants.
 */

export const BRANDING = {
  name: 'The Reading Room',
  productName: 'The Reading Room',
  tagline: 'Editorial Document Intelligence',
  subtitle: 'A quiet, considered workspace for questioning texts and tracing evidence back to the page.',
  collectionSubtitle: 'A quiet, considered workspace for questioning texts and tracing evidence back to the page.',
  version: '1.0.0',
  defaultMaxUploadSizeMb: 15,
  uploadLimitMb: 15,
  uploadLimitBytes: 15 * 1024 * 1024,
  maxQuestionLength: 2000,
  maxQuestionChars: 2000,
  suggestedQuestions: [
    'What is the central argument or primary objective of this document?',
    'What key methodologies or findings are highlighted?',
    'Which pages provide the crucial supporting evidence?',
  ],
} as const;
