/**
 * LaTeX/文本渲染工具
 * 将包含 $...$ 和 $$...$$ LaTeX 公式的文本渲染为 HTML
 */
import katex from 'katex'

// KaTeX CSS 只需加载一次
let katexCssLoaded = false
function ensureKatexCss() {
  if (katexCssLoaded) return
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css'
  document.head.appendChild(link)
  katexCssLoaded = true
}

/**
 * 渲染包含 LaTeX 公式的文本为 HTML
 * 支持 $...$ (行内) 和 $$...$$ (块级)
 */
export function renderLatexText(text) {
  if (!text) return ''
  ensureKatexCss()

  // 转义 HTML 特殊字符（防止 XSS）
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 先处理换行，避免 <br> 混入 KaTeX 生成的 SVG 中
  escaped = escaped.replace(/\n/g, '<br>')

  // 渲染块级公式 $$...$$
  escaped = escaped.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })

  // 渲染行内公式 $...$
  escaped = escaped.replace(/\$([^\$\n]+?)\$/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
      })
    } catch {
      return `<code>${formula}</code>`
    }
  })

  return escaped
}
