'use client';

/**
 * Tool Call Display Component (AG-UI Protocol)
 *
 * Displays tool calls with transparency, showing arguments and results.
 * Part of Phase 0 AG-UI Protocol implementation.
 *
 * Features:
 * - Collapsible accordion for each tool call
 * - Syntax-highlighted JSON display for args/results
 * - Status indicators (pending, running, completed, error)
 * - "Inspect Source" toggle
 * - Copy to clipboard functionality
 */

import { useState } from 'react';
import { useAgentState } from '@/hooks/useAgentState';
import { ToolCall, ToolCallStatus } from '@/types/agent';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Copy,
  Check,
} from 'lucide-react';

/**
 * Get status badge variant and icon
 */
function getStatusDisplay(status: ToolCallStatus): {
  icon: React.ReactNode;
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  label: string;
} {
  switch (status) {
    case 'pending':
      return {
        icon: <Clock className="h-3 w-3" />,
        variant: 'outline',
        label: 'Pending',
      };
    case 'running':
      return {
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        variant: 'default',
        label: 'Running',
      };
    case 'completed':
      return {
        icon: <CheckCircle2 className="h-3 w-3" />,
        variant: 'secondary',
        label: 'Completed',
      };
    case 'error':
      return {
        icon: <XCircle className="h-3 w-3" />,
        variant: 'destructive',
        label: 'Error',
      };
    default:
      return {
        icon: <Clock className="h-3 w-3" />,
        variant: 'outline',
        label: status,
      };
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

/**
 * Tool Call Item Component
 */
function ToolCallItem({ toolCall }: { toolCall: ToolCall }) {
  const [copiedArgs, setCopiedArgs] = useState(false);
  const [copiedResult, setCopiedResult] = useState(false);

  const { icon, variant, label } = getStatusDisplay(toolCall.status);

  const copyToClipboard = async (text: string, type: 'args' | 'result') => {
    await navigator.clipboard.writeText(text);
    if (type === 'args') {
      setCopiedArgs(true);
      setTimeout(() => setCopiedArgs(false), 2000);
    } else {
      setCopiedResult(true);
      setTimeout(() => setCopiedResult(false), 2000);
    }
  };

  const argsJson = JSON.stringify(toolCall.args, null, 2);
  const resultJson =
    typeof toolCall.result === 'string'
      ? toolCall.result
      : JSON.stringify(toolCall.result, null, 2);

  return (
    <AccordionItem value={toolCall.id} className="border-b">
      <AccordionTrigger className="hover:no-underline py-3">
        <div className="flex items-center justify-between w-full pr-2">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-medium">
              {toolCall.name}
            </span>
            <Badge variant={variant} className="flex items-center gap-1">
              {icon}
              <span className="text-xs">{label}</span>
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {toolCall.started_at && (
              <span>{formatTimestamp(toolCall.started_at)}</span>
            )}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pb-4">
        {/* Tool Call Arguments */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              Arguments
            </span>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2"
              onClick={() => copyToClipboard(argsJson, 'args')}
            >
              {copiedArgs ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
          </div>
          <pre className="p-3 bg-muted rounded-md text-xs overflow-x-auto font-mono">
            {argsJson}
          </pre>
        </div>

        {/* Tool Call Result */}
        {toolCall.result && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                Result
              </span>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2"
                onClick={() => copyToClipboard(resultJson, 'result')}
              >
                {copiedResult ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>
            <ScrollArea className="h-[200px]">
              <pre className="p-3 bg-muted rounded-md text-xs font-mono">
                {resultJson}
              </pre>
            </ScrollArea>
          </div>
        )}

        {/* Tool Call Error */}
        {toolCall.error && (
          <div className="space-y-2">
            <span className="text-sm font-medium text-destructive">Error</span>
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">
                {toolCall.error.type}
              </p>
              <p className="text-xs text-destructive/80 mt-1">
                {toolCall.error.message}
              </p>
            </div>
          </div>
        )}

        {/* Execution Time */}
        {toolCall.started_at && toolCall.completed_at && (
          <div className="text-xs text-muted-foreground">
            Executed in{' '}
            {Math.abs(
              new Date(toolCall.completed_at).getTime() -
                new Date(toolCall.started_at).getTime()
            )}
            ms
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}

/**
 * Tool Call Display Component
 */
export default function ToolCallDisplay() {
  const { active_thread_id, threads } = useAgentState();

  // Get tool calls from active thread
  const thread = active_thread_id ? threads[active_thread_id] : null;
  const toolCalls: ToolCall[] = thread ? thread.tool_calls : [];

  if (toolCalls.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Tool Calls</CardTitle>
          <CardDescription>
            Tool executions will appear here
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No tool calls yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Tool Calls</CardTitle>
        <CardDescription>
          {toolCalls.length} tool{toolCalls.length !== 1 ? 's' : ''} executed
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[600px] pr-4">
          <Accordion type="single" collapsible className="w-full">
            {toolCalls.map((toolCall) => (
              <ToolCallItem key={toolCall.id} toolCall={toolCall} />
            ))}
          </Accordion>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
