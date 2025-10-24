'use client';

/**
 * Progress Tracker Component (AG-UI Protocol)
 *
 * Displays real-time agent execution steps and progress.
 * Part of Phase 0 AG-UI Protocol implementation.
 *
 * Features:
 * - Ordered list of agent steps/subtasks
 * - Status indicators per step (pending, running, completed, error)
 * - Timestamps (started_at, completed_at)
 * - Animated progress indicator for current step
 * - Collapsible completed steps
 */

import { useAgentState } from '@/hooks/useAgentState';
import { AgentStep } from '@/types/agent';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Circle,
} from 'lucide-react';

/**
 * Get status icon and color
 */
function getStatusDisplay(
  status: 'pending' | 'running' | 'completed' | 'error'
): {
  icon: React.ReactNode;
  color: string;
  label: string;
} {
  switch (status) {
    case 'pending':
      return {
        icon: <Circle className="h-4 w-4" />,
        color: 'text-muted-foreground',
        label: 'Pending',
      };
    case 'running':
      return {
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        color: 'text-blue-500',
        label: 'Running',
      };
    case 'completed':
      return {
        icon: <CheckCircle2 className="h-4 w-4" />,
        color: 'text-green-500',
        label: 'Completed',
      };
    case 'error':
      return {
        icon: <XCircle className="h-4 w-4" />,
        color: 'text-destructive',
        label: 'Error',
      };
    default:
      return {
        icon: <Clock className="h-4 w-4" />,
        color: 'text-muted-foreground',
        label: status,
      };
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

/**
 * Calculate duration between two timestamps
 */
function calculateDuration(start?: string, end?: string): string {
  if (!start || !end) return '';
  const duration =
    new Date(end).getTime() - new Date(start).getTime();
  if (duration < 1000) return `${duration}ms`;
  return `${(duration / 1000).toFixed(2)}s`;
}

/**
 * Progress Step Item Component
 */
function ProgressStepItem({
  step,
  index,
  isLast,
}: {
  step: AgentStep;
  index: number;
  isLast: boolean;
}) {
  const { icon, color, label } = getStatusDisplay(step.status);
  const duration = calculateDuration(step.started_at, step.completed_at);

  return (
    <div className="relative">
      {/* Step indicator and connector line */}
      <div className="flex items-start gap-3">
        {/* Status icon with vertical line */}
        <div className="flex flex-col items-center">
          <div className={`${color} flex-shrink-0`}>{icon}</div>
          {!isLast && (
            <div
              className={`w-0.5 h-full mt-2 ${
                step.status === 'completed'
                  ? 'bg-green-500/30'
                  : 'bg-border'
              }`}
              style={{ minHeight: '24px' }}
            />
          )}
        </div>

        {/* Step content */}
        <div className="flex-1 pb-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{step.name}</p>
              {step.started_at && (
                <p className="text-xs text-muted-foreground">
                  {formatTimestamp(step.started_at)}
                  {duration && ` • ${duration}`}
                </p>
              )}
            </div>
            <Badge
              variant={
                step.status === 'completed'
                  ? 'secondary'
                  : step.status === 'error'
                  ? 'destructive'
                  : 'outline'
              }
              className="text-xs flex-shrink-0"
            >
              {label}
            </Badge>
          </div>

          {/* Metadata */}
          {step.metadata && Object.keys(step.metadata).length > 0 && (
            <div className="mt-2 p-2 bg-muted/50 rounded text-xs text-muted-foreground">
              {Object.entries(step.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="font-medium">{key}:</span>
                  <span>{String(value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Progress Tracker Component
 */
export default function ProgressTracker() {
  const { active_thread_id, threads } = useAgentState();

  // Get steps from active thread
  const thread = active_thread_id ? threads[active_thread_id] : null;
  const steps: AgentStep[] = thread ? thread.steps : [];

  // Count step statuses
  const completed = steps.filter((s) => s.status === 'completed').length;
  const running = steps.filter((s) => s.status === 'running').length;
  const errors = steps.filter((s) => s.status === 'error').length;

  if (steps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Progress</CardTitle>
          <CardDescription>Agent execution steps</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No steps yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Progress</CardTitle>
        <CardDescription>
          {completed} of {steps.length} steps completed
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Progress summary */}
        <div className="flex items-center gap-4 mb-4">
          {running > 0 && (
            <div className="flex items-center gap-1 text-xs text-blue-500">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>{running} running</span>
            </div>
          )}
          {completed > 0 && (
            <div className="flex items-center gap-1 text-xs text-green-500">
              <CheckCircle2 className="h-3 w-3" />
              <span>{completed} completed</span>
            </div>
          )}
          {errors > 0 && (
            <div className="flex items-center gap-1 text-xs text-destructive">
              <XCircle className="h-3 w-3" />
              <span>{errors} errors</span>
            </div>
          )}
        </div>

        <Separator className="mb-4" />

        {/* Progress steps list */}
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-0">
            {steps.map((step, index) => (
              <ProgressStepItem
                key={step.id}
                step={step}
                index={index}
                isLast={index === steps.length - 1}
              />
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
