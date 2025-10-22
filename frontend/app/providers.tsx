/**
 * Client-side Providers
 *
 * This component wraps the app with client-side providers like CopilotKit.
 * Separated from layout.tsx to maintain server component benefits.
 */

'use client';

import { CopilotKit } from '@copilotkit/react-core';
import '@copilotkit/react-ui/styles.css';
import './copilotkit-theme.css';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="deepAgent">
      {children}
    </CopilotKit>
  );
}
