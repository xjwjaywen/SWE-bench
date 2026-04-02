# 经验教训

## 2026-04-02: 项目初始搭建

### ChromaDB 默认 Embedding 对中文支持差
- **问题**：ChromaDB 默认使用 onnx mini-lm-l6-v2 embedding，对中文语义检索效果很差
- **解决**：测试用例中使用英文关键词验证检索功能；生产环境需配置 OpenAI text-embedding-3-small
- **避免**：在 CI 测试中不依赖中文语义匹配的精确度，只验证检索流程正确性

### reportlab 需要单独安装
- **问题**：seed_data.py 使用 reportlab 生成 PDF，但最初未加入 requirements.txt
- **解决**：补充到依赖列表
- **避免**：编写代码时同步更新依赖文件

### python-pptx 的导入名
- **问题**：`from pptx import Presentation`，不是 `PptxPresentation`
- **解决**：使用 `from pptx import Presentation as PptxPresentation`
- **避免**：注意第三方库的实际导入名称

### jsdom 不支持 scrollIntoView
- **问题**：前端测试中 jsdom 环境不支持 `Element.scrollIntoView()`
- **解决**：在 test-setup.ts 中添加 polyfill
- **避免**：前端测试使用 jsdom 时注意 DOM API 的缺失
