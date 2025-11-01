/**
 * Mock Chat Service for Testing Without Backend
 */

import { ChatRequest, ChatResponse } from '@/types';
import { mockDocumentsService } from './mock-documents.service';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Sample responses based on common questions
const generateMockResponse = (question: string, documentIds: string[]): string => {
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes('what') || lowerQuestion.includes('explain')) {
    return `Based on the selected documents, the main concept revolves around fundamental principles and their practical applications. The documents provide comprehensive coverage of key topics, including detailed explanations and real-world examples. This information is particularly relevant to understanding the core concepts and how they can be applied in various scenarios.`;
  }
  
  if (lowerQuestion.includes('how')) {
    return `To accomplish this, you should follow these steps:\n\n1. First, understand the fundamental concepts outlined in the documents\n2. Apply the principles to your specific use case\n3. Reference the best practices mentioned throughout the material\n4. Iterate and refine based on the guidelines provided\n\nThe documents contain detailed instructions and examples that can guide you through this process.`;
  }
  
  if (lowerQuestion.includes('why')) {
    return `There are several important reasons:\n\n• It provides a solid foundation for understanding the subject matter\n• It enables practical application in real-world scenarios\n• It follows industry best practices and standards\n• It helps avoid common pitfalls and mistakes\n\nThe selected documents elaborate on these points with specific examples and case studies.`;
  }
  
  if (lowerQuestion.includes('compare') || lowerQuestion.includes('difference')) {
    return `When comparing these concepts, there are key distinctions:\n\n**Approach A:**\n- Focuses on immediate implementation\n- Better for quick prototyping\n- May require later optimization\n\n**Approach B:**\n- Emphasizes long-term scalability\n- Requires more upfront planning\n- Provides better maintainability\n\nBoth approaches are discussed in detail across the selected documents, with specific use cases for each.`;
  }
  
  // Default response
  return `According to the selected documents, ${question.slice(0, 100)}... is an important topic. The documents provide detailed information covering various aspects including practical applications, theoretical foundations, and real-world examples. For more specific information, you can refer to the relevant sections highlighted in the source citations below.`;
};

const generateMockSources = (documentIds: string[]): ChatResponse['sources'] => {
  return documentIds.slice(0, 2).map((docId, index) => ({
    document_id: docId,
    page: index + 1,
    score: 0.85 - (index * 0.1),
  }));
};

export const mockChatService = {
  /**
   * Send a chat message (mock)
   */
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    await delay(1500); // Simulate AI thinking time

    // Validate that documents exist
    try {
      for (const docId of data.document_ids) {
        await mockDocumentsService.getDocument(docId);
      }
    } catch (error) {
      throw new Error('One or more selected documents not found');
    }

    // Generate response
    const response = generateMockResponse(data.query, data.document_ids);
    const sources = generateMockSources(data.document_ids);

    return {
      answer: response,
      sources: sources,
    };
  },

  /**
   * Generate a sample conversation for testing
   */
  getSampleConversation: () => {
    return [
      {
        role: 'user',
        content: 'What are the main concepts covered in these documents?',
      },
      {
        role: 'assistant',
        content: 'Based on the selected documents, the main concepts include fundamental principles, practical applications, and best practices. The documents provide comprehensive coverage with detailed examples and case studies.',
        sources: [
          { document_id: 'doc1', page: 1, score: 0.92 },
          { document_id: 'doc2', page: 3, score: 0.85 },
        ],
      },
      {
        role: 'user',
        content: 'How can I apply this knowledge?',
      },
      {
        role: 'assistant',
        content: 'You can apply this knowledge by following the step-by-step guides provided in the documents. Start with understanding the core concepts, then move to practical implementation using the examples provided. The documents also include common pitfalls to avoid.',
        sources: [
          { document_id: 'doc1', page: 5, score: 0.88 },
        ],
      },
    ];
  },
};
