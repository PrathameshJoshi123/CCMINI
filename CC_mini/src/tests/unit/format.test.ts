import { describe, it, expect } from 'vitest';
import { formatDate, formatRelativeTime, formatFileSize, truncateText } from '@/utils/format';

describe('Format Utilities', () => {
  describe('formatDate', () => {
    it('formats date string correctly', () => {
      const dateString = '2025-10-12T10:30:00Z';
      const formatted = formatDate(dateString);
      expect(formatted).toContain('Oct');
      expect(formatted).toContain('12');
      expect(formatted).toContain('2025');
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1024 * 1024)).toBe('1 MB');
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
    });

    it('formats with decimal places', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB');
      expect(formatFileSize(1024 * 1024 * 1.5)).toBe('1.5 MB');
    });
  });

  describe('truncateText', () => {
    it('truncates text longer than max length', () => {
      const text = 'This is a very long text that should be truncated';
      const truncated = truncateText(text, 20);
      expect(truncated).toBe('This is a very long ...');
      expect(truncated.length).toBeLessThanOrEqual(23); // 20 + '...'
    });

    it('does not truncate text shorter than max length', () => {
      const text = 'Short text';
      const truncated = truncateText(text, 20);
      expect(truncated).toBe('Short text');
    });
  });
});
