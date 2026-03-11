/**
 * Extract key legal topic from user message for case search.
 *
 * @param userMessage - The user's message text
 * @returns Extracted query for case search
 */
export function extractKeyQuestion(userMessage: string): string {
  // Remove common prefixes
  const cleaned = userMessage
    .replace(/我想了解|我想知道|请问|什么是|怎么/g, '')
    .trim();

  // Return first ~20 chars plus " 相关案例"
  if (cleaned.length > 20) {
    return cleaned.slice(0, 20) + " 相关案例";
  }

  return cleaned + " 相关案例";
}

/**
 * Check if a message is a legal consultation response.
 *
 * @param message - The assistant's message content
 * @returns True if this appears to be legal consultation
 */
export function isLegalConsultation(message: string): boolean {
  const legalKeywords = [
    '法律', '法规', '合同', '侵权', '赔偿', '责任',
    '起诉', '诉讼', '法院', '判决', '案例', '裁判',
    '劳动', '民事', '刑事', '行政', '纠纷', '债务',
    '房产', '离婚', '继承', '交通', '工伤', '社保',
    '民法', '刑法', '宪法'
  ];

  return legalKeywords.some(keyword => message.includes(keyword));
}
