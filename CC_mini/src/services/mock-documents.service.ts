/**
 * Mock Documents Service for Testing Without Backend
 */

import { Document, UploadResponse, GeneratedContent, ProcessingStatus } from '@/types';

const MOCK_DOCUMENTS_KEY = 'mock_documents';
const MOCK_CONTENT_KEY = 'mock_generated_content';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Get current user email from storage
const getCurrentUserEmail = (): string => {
  return localStorage.getItem('user_email') || 'test@example.com';
};

const getMockDocuments = (): Document[] => {
  const docs = localStorage.getItem(MOCK_DOCUMENTS_KEY);
  return docs ? JSON.parse(docs) : [];
};

const saveMockDocuments = (docs: Document[]) => {
  localStorage.setItem(MOCK_DOCUMENTS_KEY, JSON.stringify(docs));
};

const getMockContent = (): GeneratedContent[] => {
  const content = localStorage.getItem(MOCK_CONTENT_KEY);
  return content ? JSON.parse(content) : [];
};

const saveMockContent = (content: GeneratedContent[]) => {
  localStorage.setItem(MOCK_CONTENT_KEY, JSON.stringify(content));
};

// Create sample documents for first-time users
const createSampleDocuments = (userEmail: string): Document[] => {
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const lastWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  return [
    {
      _id: 'doc1',
      user_id: userEmail,
      original_filename: 'Machine Learning Basics.pdf',
      local_path: '/mock/ml-basics.pdf',
      processing_status: 'COMPLETED',
      uploaded_at: lastWeek.toISOString(),
    },
    {
      _id: 'doc2',
      user_id: userEmail,
      original_filename: 'React Development Guide.pdf',
      local_path: '/mock/react-guide.pdf',
      processing_status: 'COMPLETED',
      uploaded_at: yesterday.toISOString(),
    },
    {
      _id: 'doc3',
      user_id: userEmail,
      original_filename: 'Python Programming.pdf',
      local_path: '/mock/python.pdf',
      processing_status: 'PROCESSING',
      uploaded_at: now.toISOString(),
    },
  ];
};

// Create sample generated content
const createSampleContent = (documentId: string): GeneratedContent[] => {
  const now = new Date();
  
  return [
    {
      _id: `content_summary_${documentId}`,
      document_id: documentId,
      user_id: getCurrentUserEmail(),
      content_type: 'SUMMARY',
      content_data: {
        summary: `This is a comprehensive summary of the document. The document covers key concepts and provides detailed explanations of important topics. 

Key Points:
• Main concept 1: Fundamental principles and their applications
• Main concept 2: Practical examples and use cases
• Main concept 3: Best practices and recommendations

The content is well-structured and provides valuable insights for learners at all levels.`,
      },
      created_at: now.toISOString(),
    },
    {
      _id: `content_mindmap_${documentId}`,
      document_id: documentId,
      user_id: getCurrentUserEmail(),
      content_type: 'MINDMAP',
      content_data: {
        nodes: [
          { id: '1', label: 'Main Topic', level: 0 },
          { id: '2', label: 'Concept 1', level: 1, parent: '1' },
          { id: '3', label: 'Concept 2', level: 1, parent: '1' },
          { id: '4', label: 'Concept 3', level: 1, parent: '1' },
          { id: '5', label: 'Subtopic 1.1', level: 2, parent: '2' },
          { id: '6', label: 'Subtopic 1.2', level: 2, parent: '2' },
          { id: '7', label: 'Subtopic 2.1', level: 2, parent: '3' },
          { id: '8', label: 'Subtopic 3.1', level: 2, parent: '4' },
        ],
        edges: [
          { from: '1', to: '2' },
          { from: '1', to: '3' },
          { from: '1', to: '4' },
          { from: '2', to: '5' },
          { from: '2', to: '6' },
          { from: '3', to: '7' },
          { from: '4', to: '8' },
        ],
      },
      created_at: now.toISOString(),
    },
    {
      _id: `content_flashcards_${documentId}`,
      document_id: documentId,
      user_id: getCurrentUserEmail(),
      content_type: 'FLASHCARDS',
      content_data: {
        flashcards: [
          {
            question: 'What is the main concept discussed in this document?',
            answer: 'The document discusses fundamental principles and their practical applications in the field.',
          },
          {
            question: 'What are the key benefits mentioned?',
            answer: 'The key benefits include improved understanding, practical implementation strategies, and real-world applications.',
          },
          {
            question: 'What best practices are recommended?',
            answer: 'The document recommends following industry standards, continuous learning, and practical experimentation.',
          },
          {
            question: 'How can this knowledge be applied?',
            answer: 'This knowledge can be applied through hands-on projects, collaborative work, and iterative improvement.',
          },
          {
            question: 'What are the common challenges?',
            answer: 'Common challenges include initial complexity, resource requirements, and the learning curve for beginners.',
          },
        ],
      },
      created_at: now.toISOString(),
    },
  ];
};

export const mockDocumentsService = {
  /**
   * Upload a document (mock)
   */
  uploadDocument: async (file: File): Promise<UploadResponse> => {
    await delay(1000);

    const userEmail = getCurrentUserEmail();
    const documents = getMockDocuments();
    
    const newDoc: Document = {
      _id: `doc_${Date.now()}`,
      user_id: userEmail,
      original_filename: file.name,
      local_path: `/mock/${file.name}`,
      processing_status: 'UPLOADING',
      uploaded_at: new Date().toISOString(),
    };

    documents.push(newDoc);
    saveMockDocuments(documents);

    // Simulate processing: UPLOADING -> PROCESSING -> COMPLETED
    setTimeout(() => {
      const docs = getMockDocuments();
      const doc = docs.find(d => d._id === newDoc._id);
      if (doc) {
        doc.processing_status = 'PROCESSING';
        saveMockDocuments(docs);
        
        // Generate content after 3 seconds
        setTimeout(() => {
          const docs2 = getMockDocuments();
          const doc2 = docs2.find(d => d._id === newDoc._id);
          if (doc2) {
            doc2.processing_status = 'COMPLETED';
            saveMockDocuments(docs2);
            
            // Create generated content
            const allContent = getMockContent();
            const newContent = createSampleContent(newDoc._id);
            saveMockContent([...allContent, ...newContent]);
          }
        }, 3000);
      }
    }, 2000);

    return {
      message: 'Document uploaded successfully',
      document_id: newDoc._id,
      filename: file.name,
      status: 'UPLOADING',
    };
  },

  /**
   * Get all documents for current user
   */
  getDocuments: async (): Promise<Document[]> => {
    await delay(500);

    const userEmail = getCurrentUserEmail();
    let documents = getMockDocuments();
    
    // Filter by current user
    documents = documents.filter(d => d.user_id === userEmail);

    // If no documents, create sample ones
    if (documents.length === 0) {
      const sampleDocs = createSampleDocuments(userEmail);
      const allDocs = getMockDocuments();
      saveMockDocuments([...allDocs, ...sampleDocs]);
      
      // Create sample content for completed docs
      const content = getMockContent();
      sampleDocs.forEach(doc => {
        if (doc.processing_status === 'COMPLETED') {
          const sampleContent = createSampleContent(doc._id);
          content.push(...sampleContent);
        }
      });
      saveMockContent(content);
      
      documents = sampleDocs;
    }

    // Sort by upload date (newest first)
    return documents.sort((a, b) => 
      new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
    );
  },

  /**
   * Get a specific document
   */
  getDocument: async (documentId: string): Promise<Document> => {
    await delay(300);

    const documents = getMockDocuments();
    const doc = documents.find(d => d._id === documentId);

    if (!doc) {
      throw new Error('Document not found');
    }

    const userEmail = getCurrentUserEmail();
    if (doc.user_id !== userEmail) {
      throw new Error('Unauthorized');
    }

    return doc;
  },

  /**
   * Get generated content for a document
   */
  getGeneratedContent: async (documentId: string): Promise<GeneratedContent[]> => {
    await delay(400);

    const allContent = getMockContent();
    const content = allContent.filter(c => c.document_id === documentId);

    // If no content exists and document is completed, create it
    if (content.length === 0) {
      const doc = await mockDocumentsService.getDocument(documentId);
      if (doc.processing_status === 'COMPLETED') {
        const newContent = createSampleContent(documentId);
        saveMockContent([...allContent, ...newContent]);
        return newContent;
      }
    }

    return content;
  },

  /**
   * Delete a document (mock)
   */
  deleteDocument: async (documentId: string): Promise<void> => {
    await delay(300);

    const documents = getMockDocuments();
    const filteredDocs = documents.filter(d => d._id !== documentId);
    saveMockDocuments(filteredDocs);

    // Also delete associated content
    const allContent = getMockContent();
    const filteredContent = allContent.filter(c => c.document_id !== documentId);
    saveMockContent(filteredContent);
  },

  /**
   * Clear all mock documents (for testing)
   */
  clearAllDocuments: (): void => {
    localStorage.removeItem(MOCK_DOCUMENTS_KEY);
    localStorage.removeItem(MOCK_CONTENT_KEY);
  },
};
