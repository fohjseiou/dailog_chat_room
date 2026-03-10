import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { Input, Select, Space, Typography } from 'antd';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

export function DocumentFilters() {
  const { filters, setSearch, setCategory } = useKnowledgeStore();

  return (
    <Space size="large" className="w-full">
      {/* Search */}
      <Search
        placeholder="搜索文档标题或来源..."
        value={filters.search}
        onChange={(e) => setSearch(e.target.value)}
        onSearch={setSearch}
        allowClear
        className="max-w-md"
      />

      {/* Category Filter */}
      <Space>
        <Text strong>分类:</Text>
        <Select
          value={filters.category}
          onChange={setCategory}
          style={{ width: 140 }}
        >
          <Option value="">全部</Option>
          <Option value="law">法律法规</Option>
          <Option value="case">案例分析</Option>
          <Option value="contract">合同范本</Option>
          <Option value="interpretation">司法解释</Option>
        </Select>
      </Space>
    </Space>
  );
}
