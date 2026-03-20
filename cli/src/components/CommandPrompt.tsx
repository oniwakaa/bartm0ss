import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';

interface CommandPromptProps {
  diff?: string;
  onApprove: () => void;
  onReject: () => void;
}

/**
 * User input + approval/block UI for apply-diff commands
 */
export const CommandPrompt: React.FC<CommandPromptProps> = ({
  diff,
  onApprove,
  onReject,
}) => {
  const [waiting, setWaiting] = useState(true);

  useInput((input) => {
    if (!waiting) return;
    const key = input.toLowerCase();
    if (key === 'y') {
      setWaiting(false);
      onApprove();
    } else if (key === 'n') {
      setWaiting(false);
      onReject();
    }
  });

  if (!diff) return null;

  return (
    <Box flexDirection="column">
      <Box borderStyle="round" borderColor="yellow">
        <Text>{diff}</Text>
      </Box>
      <Text>
        Apply this diff? [<Text color="green">Y</Text>/{' '}
        <Text color="red">n</Text>]
      </Text>
    </Box>
  );
};

export default CommandPrompt;