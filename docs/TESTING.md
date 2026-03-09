# 测试指南

本文档提供了法律咨询助手平台的完整测试指南。

## 目录

- [测试概述](#测试概述)
- [后端测试](#后端测试)
- [前端测试](#前端测试)
- [API 集成测试](#api-集成测试)
- [E2E 测试](#e2e-测试)
- [测试覆盖率](#测试覆盖率)
- [持续集成](#持续集成)

---

## 测试概述

### 测试策略

本项目采用多层次测试策略：

```
┌─────────────────────────────────────────┐
│          E2E Tests (Playwright)         │
│         (用户流程端到端测试)              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Integration Tests (Vitest)         │
│         (API 和组件集成测试)              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Unit Tests (Vitest/pytest)      │
│        (单元测试 - 函数/组件)            │
└─────────────────────────────────────────┘
```

### 测试覆盖率目标

| 层级 | 语句覆盖率 | 分支覆盖率 | 函数覆盖率 | 行覆盖率 |
|------|-----------|-----------|-----------|---------|
| 后端 | 80% | 75% | 80% | 80% |
| 前端 | 70% | 65% | 70% | 70% |
| 总体 | 75% | 70% | 75% | 75% |

---

## 后端测试

### 运行后端测试

```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_knowledge_api.py -v

# 运行测试并查看覆盖率
pytest tests/ --cov=app --cov-report=html

# 运行特定测试
pytest tests/test_knowledge_api.py::test_list_documents -v
```

### 后端测试文件结构

```
backend/tests/
├── test_knowledge_api.py      # 知识库 API 测试
├── test_streaming.py           # SSE 流式响应测试
├── test_summary_service.py     # 摘要服务测试
├── conftest.py                 # pytest 配置和 fixtures
└── __init__.py
```

### 后端测试示例

#### API 测试

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_list_documents():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/knowledge/documents")
        assert response.status_code == 200
        assert "items" in response.json()
```

#### Service 测试

```python
import pytest
from app.services.summary_service import SummaryService

@pytest.mark.asyncio
async def test_generate_summary():
    service = SummaryService()
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助您的？"}
    ]
    summary = await service.generate_summary(messages)
    assert summary is not None
    assert len(summary) > 0
```

---

## 前端测试

### 运行前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并监听变化
npm test -- --watch

# 运行测试并查看 UI
npm run test:ui

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行特定测试文件
npm test -- Button.test.tsx
```

### 前端测试文件结构

```
frontend/src/
├── test/
│   ├── setup.ts           # 测试设置
│   └── test-utils.tsx     # 测试工具函数
├── components/
│   ├── ui/
│   │   ├── Button.test.tsx
│   │   ├── Skeleton.test.tsx
│   │   ├── Alert.test.tsx
│   │   └── Transition.test.tsx
│   ├── chat/
│   │   ├── MessageBubble.test.tsx
│   │   └── ThinkingIndicator.test.tsx
│   └── knowledge/
│       ├── StatsPanel.test.tsx
│       └── DocumentCard.test.tsx
└── stores/
    └── (store tests)
```

### 前端测试示例

#### 组件测试

```typescript
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/test-utils';
import { TouchButton } from './Button';

describe('TouchButton', () => {
  it('renders children correctly', () => {
    renderWithProviders(<TouchButton>Click me</TouchButton>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    renderWithProviders(<TouchButton onClick={handleClick}>Click me</TouchButton>);

    await userEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### Store 测试

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chatStore';

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useChatStore.getState().reset();
  });

  it('adds message to store', () => {
    const store = useChatStore.getState();

    store.addMessage({
      id: '1',
      role: 'user',
      content: 'Hello',
      timestamp: new Date().toISOString(),
    });

    expect(store.messages).toHaveLength(1);
    expect(store.messages[0].content).toBe('Hello');
  });
});
```

---

## API 集成测试

### 创建集成测试

**`frontend/tests/integration/api.integration.test.ts`**:

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { knowledgeApi } from '../src/api/client';

describe('Knowledge API Integration', () => {
  let createdDocId: string;

  it('should fetch documents', async () => {
    const result = await knowledgeApi.getDocuments({ page: 1, page_size: 10 });
    expect(result.items).toBeInstanceOf(Array);
  });

  it('should create document', async () => {
    const doc = await knowledgeApi.createDocument({
      title: 'Test Document',
      category: 'law',
      source: 'Test Source',
    });
    createdDocId = doc.id;
    expect(doc.id).toBeDefined();
  });

  it('should delete document', async () => {
    await knowledgeApi.deleteDocument(createdDocId);
    // Verify deletion
    const result = await knowledgeApi.getDocuments({ page: 1, page_size: 10 });
    expect(result.items.find((d) => d.id === createdDocId)).toBeUndefined();
  });
});
```

---

## E2E 测试

### 设置 Playwright

```bash
npm install -D @playwright/test
npx playwright install
```

### 创建 E2E 测试

**`frontend/tests/e2e/chat.spec.ts`**:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test('user can send and receive messages', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Send a message
    await page.fill('[data-testid="message-input"]', '你好');
    await page.click('[data-testid="send-button"]');

    // Wait for response
    await expect(page.locator('[data-testid="message-bubble"]')).toContainText('你好');
  });

  test('displays thinking indicator', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await page.fill('[data-testid="message-input"]', '什么是合同法？');
    await page.click('[data-testid="send-button"]');

    // Check for thinking indicator
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeVisible();
  });
});
```

**`frontend/tests/e2e/knowledge.spec.ts`**:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Knowledge Management', () => {
  test('user can upload and manage documents', async ({ page }) => {
    await page.goto('http://localhost:5173/knowledge');

    // Click upload button
    await page.click('[data-testid="upload-button"]');

    // Select file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-files/document.pdf');

    // Fill metadata
    await page.fill('[data-testid="doc-title"]', 'Test Document');
    await page.selectOption('[data-testid="doc-category"]', 'law');

    // Submit
    await page.click('[data-testid="submit-upload"]');

    // Verify document appears
    await expect(page.locator('text=Test Document')).toBeVisible();
  });
});
```

### 运行 E2E 测试

```bash
# 运行所有 E2E 测试
npx playwright test

# 运行特定测试文件
npx playwright test chat.spec.ts

# 以 UI 模式运行
npx playwright test --ui

# 生成测试报告
npx playwright show-report
```

---

## 测试覆盖率

### 查看覆盖率报告

**后端：**

```bash
pytest tests/ --cov=app --cov-report=html
# 打开 htmlcov/index.html
```

**前端：**

```bash
npm run test:coverage
# 打开 coverage/index.html
```

### 覆盖率徽章

在 README.md 中添加覆盖率徽章：

```markdown
![Backend Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)
![Frontend Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen)
```

---

## 持续集成

### GitHub Actions 配置

**`.github/workflows/test.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=lcov
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps
      - name: Install backend
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Start services
        run: |
          cd backend && uvicorn app.main:app &
          cd frontend && npm run dev &
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## 测试最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 格式：`should_[期望行为]_when_[条件]`

```typescript
// ❌ 不好
it('test button', () => {});

// ✅ 好
it('should call onClick handler when clicked and not disabled', () => {});
```

### 2. 测试隔离

- 每个测试应该独立运行
- 使用 `beforeEach` 重置状态

```typescript
beforeEach(() => {
  // Reset store
  useChatStore.getState().reset();
  // Clear mocks
  vi.clearAllMocks();
});
```

### 3. 避免测试实现细节

- 测试用户行为，而非实现细节

```typescript
// ❌ 不好 - 测试内部状态
it('should set loading to true', () => {
  expect(store.loading).toBe(true);
});

// ✅ 好 - 测试用户可见行为
it('should show loading spinner', () => {
  expect(screen.getByTestId('loading-spinner')).toBeVisible();
});
```

### 4. 使用测试专用工具

- 使用 `data-testid` 属性选择元素
- 避免依赖 CSS 类名

```tsx
<button data-testid="submit-button">提交</button>
```

```typescript
// ✅ 稳定
screen.getByTestId('submit-button')

// ❌ 不稳定 - CSS 类名可能改变
screen.getByClassName('btn-primary')
```

### 5. Mock 外部依赖

- Mock API 调用
- Mock 浏览器 API

```typescript
vi.mock('../api/client', () => ({
  knowledgeApi: {
    getDocuments: vi.fn().mockResolvedValue({ items: [] }),
  },
}));
```

---

## 故障排查

### 常见问题

#### 1. 测试超时

```typescript
// 增加超时时间
it('should load data', async () => {
  // ...
}, { timeout: 10000 });
```

#### 2. Async 测试未完成

```typescript
// 确保等待所有异步操作
await waitFor(() => {
  expect(element).toBeVisible();
});
```

#### 3. Mock 未生效

```typescript
// 在测试文件顶部 mock
vi.mock('../module', () => ({ ... }));

// 或者重置 mock
beforeEach(() => {
  vi.clearAllMocks();
});
```

---

## 资源

- [Vitest 文档](https://vitest.dev/)
- [Testing Library 文档](https://testing-library.com/)
- [Playwright 文档](https://playwright.dev/)
- [pytest 文档](https://docs.pytest.org/)
