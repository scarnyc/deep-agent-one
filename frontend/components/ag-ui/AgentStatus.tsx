'use client';

/**
 * Agent Status Component (AG-UI Protocol)
 *
 * Displays the overall agent execution state and metadata.
 * Part of Phase 0 AG-UI Protocol implementation.
 *
 * Features:
 * - Status badge (idle, running, waiting_for_approval, completed, error)
 * - Color-coded states with pulse animation for "running"
 * - Reasoning effort indicator (low/medium/high)
 * - Token usage display
 * - Connection status
 */

import { useAgentState } from '@/hooks/useAgentState';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AgentStatus as AgentStatusType } from '@/types/agent';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Circle,
  Pause,
  Wifi,
  WifiOff,
} from 'lucide-react';

/**
 * Get status display properties
 */
function getStatusDisplay(status: AgentStatusType): {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  label: string;
  pulse: boolean;
} {
  switch (status) {
    case 'idle':
      return {
        icon: <Circle className="h-4 w-4" />,
        color: 'text-muted-foreground',
        bgColor: 'bg-muted',
        label: 'Idle',
        pulse: false,
      };
    case 'running':
      return {
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        color: 'text-blue-500',
        bgColor: 'bg-blue-500/10',
        label: 'Running',
        pulse: true,
      };
    case 'waiting_for_approval':
      return {
        icon: <Pause className="h-4 w-4" />,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500/10',
        label: 'Awaiting Approval',
        pulse: true,
      };
    case 'completed':
      return {
        icon: <CheckCircle2 className="h-4 w-4" />,
        color: 'text-green-500',
        bgColor: 'bg-green-500/10',
        label: 'Completed',
        pulse: false,
      };
    case 'error':
      return {
        icon: <XCircle className="h-4 w-4" />,
        color: 'text-destructive',
        bgColor: 'bg-destructive/10',
        label: 'Error',
        pulse: false,
      };
    default:
      return {
        icon: <Circle className="h-4 w-4" />,
        color: 'text-muted-foreground',
        bgColor: 'bg-muted',
        label: status,
        pulse: false,
      };
  }
}

/**
 * Get connection status display
 */
function getConnectionDisplay(
  status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'
): {
  icon: React.ReactNode;
  color: string;
  label: string;
} {
  switch (status) {
    case 'connected':
      return {
        icon: <Wifi className="h-3 w-3" />,
        color: 'text-green-500',
        label: 'Connected',
      };
    case 'connecting':
    case 'reconnecting':
      return {
        icon: <Loader2 className="h-3 w-3 animate-spin" />,
        color: 'text-yellow-500',
        label: status === 'connecting' ? 'Connecting' : 'Reconnecting',
      };
    case 'disconnected':
    case 'error':
      return {
        icon: <WifiOff className="h-3 w-3" />,
        color: 'text-destructive',
        label: 'Disconnected',
      };
    default:
      return {
        icon: <Circle className="h-3 w-3" />,
        color: 'text-muted-foreground',
        label: status,
      };
  }
}

/**
 * Get reasoning effort badge color
 */
function getReasoningEffortColor(
  effort?: 'low' | 'medium' | 'high'
): string {
  switch (effort) {
    case 'low':
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case 'high':
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    default:
      return 'bg-muted text-muted-foreground';
  }
}

/**
 * Agent Status Component
 */
export default function AgentStatus() {
  const { active_thread_id, threads } = useAgentState();
  const { connectionStatus } = useWebSocket();

  // Get thread data
  const thread = active_thread_id ? threads[active_thread_id] : null;
  const agentStatus: AgentStatusType = thread?.agent_status || 'idle';

  // Extract metadata from the most recent assistant message
  const lastAssistantMessage = thread?.messages
    .filter((m) => m.role === 'assistant')
    .pop();
  const reasoningEffort = lastAssistantMessage?.metadata?.reasoning_effort as
    | 'low'
    | 'medium'
    | 'high'
    | undefined;
  const tokensUsed = lastAssistantMessage?.metadata?.tokens_used as number | undefined;
  const model = lastAssistantMessage?.metadata?.model as string | undefined;

  const { icon, color, bgColor, label, pulse } =
    getStatusDisplay(agentStatus);
  const connectionDisplay = getConnectionDisplay(connectionStatus);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Agent Status</CardTitle>
        <CardDescription>Current execution state</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Status Badge */}
        <div
          className={`flex items-center justify-between p-3 rounded-lg ${bgColor} ${
            pulse ? 'animate-pulse' : ''
          }`}
        >
          <div className="flex items-center gap-2">
            <div className={color}>{icon}</div>
            <span className={`text-sm font-medium ${color}`}>{label}</span>
          </div>
        </div>

        <Separator />

        {/* Connection Status */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Connection</span>
          <div className="flex items-center gap-1">
            <div className={connectionDisplay.color}>
              {connectionDisplay.icon}
            </div>
            <span className={connectionDisplay.color}>
              {connectionDisplay.label}
            </span>
          </div>
        </div>

        {/* Reasoning Effort */}
        {reasoningEffort && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Reasoning Effort</span>
            <Badge
              variant="outline"
              className={`text-xs ${getReasoningEffortColor(reasoningEffort)}`}
            >
              {reasoningEffort.toUpperCase()}
            </Badge>
          </div>
        )}

        {/* Model */}
        {model && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Model</span>
            <span className="font-mono text-muted-foreground">{model}</span>
          </div>
        )}

        {/* Token Usage */}
        {tokensUsed !== undefined && tokensUsed > 0 && (
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Tokens Used</span>
            <span className="font-mono text-muted-foreground">
              {tokensUsed.toLocaleString()}
            </span>
          </div>
        )}

        {/* Thread ID (for debugging) */}
        {active_thread_id && (
          <>
            <Separator />
            <div className="text-xs text-muted-foreground">
              <span className="block mb-1">Thread ID</span>
              <code className="block p-2 bg-muted rounded text-[10px] font-mono break-all">
                {active_thread_id}
              </code>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
