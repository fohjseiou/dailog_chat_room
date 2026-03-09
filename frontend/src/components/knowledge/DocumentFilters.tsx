import { useKnowledgeStore } from '../../stores/knowledgeStore';

export function DocumentFilters() {
  const { filters, setSearch, setCategory } = useKnowledgeStore();

  return (
    <div className="flex items-center gap-4">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <input
            type="text"
            placeholder="搜索文档标题或来源..."
            value={filters.search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">分类:</label>
        <select
          value={filters.category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">全部</option>
          <option value="law">法律法规</option>
          <option value="case">案例分析</option>
          <option value="contract">合同范本</option>
          <option value="interpretation">司法解释</option>
        </select>
      </div>
    </div>
  );
}
