'use client';

/**
 * Markdown Content Component
 *
 * Renders markdown text with proper formatting including:
 * - Headers (h1-h6)
 * - Bold, italic, strikethrough
 * - Links (clickable, open in new tab)
 * - Code blocks and inline code
 * - Lists (ordered and unordered)
 * - Blockquotes
 * - Horizontal rules
 * - Tables (GFM)
 *
 * Uses react-markdown with remark-gfm for GitHub Flavored Markdown support.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * Custom component overrides for markdown rendering
 */
const markdownComponents: Components = {
  // Headers
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold mt-6 mb-4 first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xl font-bold mt-5 mb-3 first:mt-0">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-semibold mt-4 mb-2 first:mt-0">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-base font-semibold mt-3 mb-2 first:mt-0">{children}</h4>
  ),
  h5: ({ children }) => (
    <h5 className="text-sm font-semibold mt-3 mb-1 first:mt-0">{children}</h5>
  ),
  h6: ({ children }) => (
    <h6 className="text-sm font-medium mt-3 mb-1 first:mt-0">{children}</h6>
  ),

  // Paragraphs
  p: ({ children }) => (
    <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
  ),

  // Links - open in new tab
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-600 dark:text-blue-400 hover:underline"
    >
      {children}
    </a>
  ),

  // Code blocks
  code: ({ className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    const isInline = !match && !className;

    if (isInline) {
      return (
        <code
          className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <code
        className={`block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto ${className || ''}`}
        {...props}
      >
        {children}
      </code>
    );
  },

  // Pre (code block wrapper)
  pre: ({ children }) => (
    <pre className="bg-muted rounded-lg my-3 overflow-x-auto">{children}</pre>
  ),

  // Lists
  ul: ({ children }) => (
    <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>
  ),
  li: ({ children }) => {
    // Skip rendering empty list items (fixes orphan bullets from malformed markdown)
    // This handles cases where LLM generates "- \n**content**" instead of "- **content**"
    const hasContent = React.Children.toArray(children).some((child) => {
      if (typeof child === 'string') {
        return child.trim().length > 0;
      }
      return child !== null && child !== undefined;
    });
    if (!hasContent) {
      return null;
    }
    return <li className="leading-relaxed">{children}</li>;
  },

  // Blockquotes
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-muted-foreground/30 pl-4 my-3 italic text-muted-foreground">
      {children}
    </blockquote>
  ),

  // Horizontal rule
  hr: () => <hr className="my-4 border-muted-foreground/30" />,

  // Tables (GFM)
  table: ({ children }) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full border-collapse border border-muted-foreground/20">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-muted">{children}</thead>
  ),
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => (
    <tr className="border-b border-muted-foreground/20">{children}</tr>
  ),
  th: ({ children }) => (
    <th className="px-4 py-2 text-left font-semibold border border-muted-foreground/20">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2 border border-muted-foreground/20">{children}</td>
  ),

  // Strong (bold)
  strong: ({ children }) => (
    <strong className="font-semibold">{children}</strong>
  ),

  // Emphasis (italic)
  em: ({ children }) => <em className="italic">{children}</em>,

  // Strikethrough (GFM)
  del: ({ children }) => <del className="line-through">{children}</del>,
};

/**
 * MarkdownContent Component
 *
 * Renders markdown content with proper formatting and styling.
 * Links open in new tabs for better UX in chat context.
 */
export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`markdown-content prose prose-sm dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownContent;
