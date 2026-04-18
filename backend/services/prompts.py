"""Prompt templates for AI-powered knowledge structuring."""

OUTLINE_GENERATION_PROMPT = """请分析以下文档内容，生成层级结构大纲。

你必须返回JSON格式，不要返回任何其他文字说明。如果文档内容很少，也至少生成一个大纲节点。

输出格式（严格遵守）：
{
  "title": "文档主标题",
  "level": 0,
  "children": [
    {
      "title": "第一章/第一部分 标题",
      "level": 1,
      "children": [
        {"title": "1.1 小节标题", "level": 2, "children": []}
      ]
    }
  ]
}

规则：
1. 根据文档内容的自然段落和语义结构划分章节
2. 如果文档有明确标题（如"第一章"、"# 标题"等），直接使用
3. 如果没有明确标题，根据段落内容总结出有意义的标题
4. 标题要简洁（不超过30字），准确概括该部分内容
5. 一般分2-4层，根节点level=0
6. 必须输出合法JSON，不要加```json```标记

文档内容：
{content}"""

KNOWLEDGE_POINT_EXTRACTION_PROMPT = """请从以下文档内容中提取知识点。

当前文档大纲：
{outline}

文档内容：
{content}

你必须返回JSON数组格式，不要返回任何其他文字说明。至少提取3个知识点。

输出格式（严格遵守）：
[
  {{
    "text": "知识点的具体内容，完整描述",
    "type": "definition",
    "importance": 3,
    "summary": "一句话概括",
    "related_concepts": ["相关概念"],
    "node_path": ["所属章节"]
  }}
]

type可选值：
- definition: 定义或概念解释
- formula: 公式或定理
- concept: 核心概念
- important: 重点内容
- example: 示例或案例
- summary: 总结归纳
- bullet: 普通要点

importance: 1=了解, 2=理解, 3=掌握, 4=熟练, 5=精通

规则：
1. 每个知识点应是一条完整的信息，4-200字
2. node_path应对应大纲中的章节路径
3. 必须输出合法JSON数组，不要加```json```标记
4. 至少提取3个知识点，即使文档内容较少
"""
