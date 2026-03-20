import React from 'react';
import { Box, Text } from 'ink';

interface StatusBarProps {
  model: string;
  mode: string;
  iteration: number;
  status: 'running' | 'waiting' | 'done' | 'error';
}

/**
 * Persistent bottom bar showing current state
 */
export const StatusBar: React.FC<StatusBarProps> = ({
  model,
  mode,
  iteration,
  status,
}) => {
  const statusColor = {
    running: 'yellow',
    waiting: 'blue',
    done: 'green',
    error: 'red',
  }[status];

  return (
    <Box>
      <Text>Model: {model} | </Text>
      <Text>Mode: {mode} | </Text>
      <Text>Iter: {iteration} | </Text>
      <Text color={statusColor}>Status: {status}</Text>
    </Box>
  );
};

export default StatusBar;