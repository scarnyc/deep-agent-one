/**
 * HITL Approval Component
 *
 * Human-in-the-Loop approval interface for sensitive agent actions.
 * Uses CopilotKit's useCopilotAction with renderAndWaitForResponse.
 */

'use client';

import { useCopilotAction } from '@copilotkit/react-core';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle, Edit, MessageSquare } from 'lucide-react';
import { useState } from 'react';

interface HITLApprovalProps {
  toolName: string;
  toolArgs: Record<string, any>;
  reason?: string;
  status: 'executing' | 'complete' | 'inProgress';
  onApprove?: (data?: { approved: boolean; metadata?: any }) => void;
}

function HITLApprovalUI({
  toolName,
  toolArgs,
  reason,
  status,
  onApprove,
}: HITLApprovalProps) {
  const [responseText, setResponseText] = useState('');
  const [editedArgs, setEditedArgs] = useState(JSON.stringify(toolArgs, null, 2));
  const [showEdit, setShowEdit] = useState(false);
  const [showRespond, setShowRespond] = useState(false);

  const handleAccept = () => {
    onApprove?.({ approved: true, metadata: { action: 'accept' } });
  };

  const handleRespond = () => {
    if (responseText.trim()) {
      onApprove?.({
        approved: false,
        metadata: { action: 'respond', responseText },
      });
    }
  };

  const handleEdit = () => {
    try {
      const parsed = JSON.parse(editedArgs);
      onApprove?.({
        approved: true,
        metadata: { action: 'edit', editedArgs: parsed },
      });
    } catch (error) {
      alert('Invalid JSON. Please fix the syntax.');
    }
  };

  if (status === 'complete') {
    return null; // Hide after approval
  }

  return (
    <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            Approval Required
          </CardTitle>
          <Badge variant="outline" className="border-yellow-600 text-yellow-600">
            HITL
          </Badge>
        </div>
        <CardDescription>
          The agent is requesting your approval to proceed with this action.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Tool Information */}
        <div>
          <p className="text-sm font-medium mb-1">Tool:</p>
          <code className="px-2 py-1 bg-secondary rounded text-sm">{toolName}</code>
        </div>

        {/* Reason */}
        {reason && (
          <Alert>
            <AlertDescription>{reason}</AlertDescription>
          </Alert>
        )}

        {/* Tool Arguments */}
        <div>
          <p className="text-sm font-medium mb-2">Arguments:</p>
          <pre className="p-3 bg-secondary rounded text-xs overflow-auto max-h-40">
            {JSON.stringify(toolArgs, null, 2)}
          </pre>
        </div>

        {/* Response Text Input */}
        {showRespond && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Your Response:</label>
            <Textarea
              value={responseText}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setResponseText(e.target.value)}
              placeholder="Provide feedback or instructions to the agent..."
              className="min-h-[100px]"
            />
          </div>
        )}

        {/* Edit Arguments */}
        {showEdit && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Edit Arguments (JSON):</label>
            <Textarea
              value={editedArgs}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditedArgs(e.target.value)}
              className="font-mono text-xs min-h-[150px]"
            />
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 flex-wrap">
        {!showRespond && !showEdit && (
          <>
            <Button
              onClick={handleAccept}
              variant="default"
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Accept
            </Button>
            <Button
              onClick={() => setShowRespond(true)}
              variant="outline"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Respond
            </Button>
            <Button
              onClick={() => setShowEdit(true)}
              variant="outline"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </>
        )}

        {showRespond && (
          <>
            <Button onClick={handleRespond} disabled={!responseText.trim()}>
              Send Response
            </Button>
            <Button
              onClick={() => {
                setShowRespond(false);
                setResponseText('');
              }}
              variant="outline"
            >
              Cancel
            </Button>
          </>
        )}

        {showEdit && (
          <>
            <Button onClick={handleEdit}>
              Approve with Edits
            </Button>
            <Button
              onClick={() => {
                setShowEdit(false);
                setEditedArgs(JSON.stringify(toolArgs, null, 2));
              }}
              variant="outline"
            >
              Cancel
            </Button>
          </>
        )}
      </CardFooter>
    </Card>
  );
}

/**
 * Setup HITL Actions with CopilotKit
 *
 * This hook registers HITL-enabled actions that require user approval.
 * The agent can call these actions, and the UI will prompt for approval.
 */
export function useHITLActions() {
  // Register file deletion action with HITL
  useCopilotAction({
    name: 'delete_file',
    description: 'Delete a file (requires user approval)',
    parameters: [
      {
        name: 'file_path',
        type: 'string',
        description: 'Path to the file to delete',
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, status, respond }) => {
      return (
        <HITLApprovalUI
          toolName="delete_file"
          toolArgs={args}
          reason="This action will permanently delete a file."
          status={status}
          onApprove={respond}
        />
      );
    },
  });

  // Register write file action with HITL
  useCopilotAction({
    name: 'write_file',
    description: 'Write content to a file (requires user approval for sensitive paths)',
    parameters: [
      {
        name: 'file_path',
        type: 'string',
        description: 'Path where the file will be written',
        required: true,
      },
      {
        name: 'content',
        type: 'string',
        description: 'Content to write to the file',
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, status, respond }) => {
      return (
        <HITLApprovalUI
          toolName="write_file"
          toolArgs={args}
          reason="This action will create or overwrite a file."
          status={status}
          onApprove={respond}
        />
      );
    },
  });

  // Add more HITL actions as needed
}
