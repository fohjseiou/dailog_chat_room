import { describe, it, expect } from 'vitest';
import { extractKeyQuestion, isLegalConsultation } from '../queryExtractor';

describe('queryExtractor', () => {
  describe('extractKeyQuestion', () => {
    it('removes common prefixes', () => {
      expect(extractKeyQuestion('我想了解劳动合同纠纷'))
        .toBe('劳动合同纠纷 相关案例');
    });

    it('truncates long messages', () => {
      const long = '这是一个非常长的关于劳动合同纠纷的问题描述';
      const result = extractKeyQuestion(long);
      expect(result.length).toBeLessThan(30);
    });

    it('adds 相关案例 suffix', () => {
      expect(extractKeyQuestion('交通事故')).toContain('相关案例');
    });

    it('handles empty string', () => {
      expect(extractKeyQuestion('')).toBe(' 相关案例');
    });
  });

  describe('isLegalConsultation', () => {
    it('returns true for legal keywords', () => {
      expect(isLegalConsultation('根据民法典相关规定')).toBe(true);
      expect(isLegalConsultation('劳动合同纠纷怎么办')).toBe(true);
      expect(isLegalConsultation('法院判决流程')).toBe(true);
    });

    it('returns false for non-legal content', () => {
      expect(isLegalConsultation('你好，今天天气不错')).toBe(false);
      expect(isLegalConsultation('how are you')).toBe(false);
    });
  });
});
