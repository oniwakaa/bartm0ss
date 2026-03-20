import React from 'react';
import { Box, Text } from 'ink';

interface AppProps {
  mode: 'task' | 'chat' | 'review' | 'refactor';
  goal?: string;
}

/**
 * Root Ink app component for bartm0ss CLI
 */
export const App: React.FC<AppProps> = ({ mode, goal }) => {
  return (
    <Box flexDirection="column">
      <Text>bartm0ss - {mode} mode</Text>
      {goal && <Text>Goal: {goal}</Text>}
    </Box>
  );
};

export default App;