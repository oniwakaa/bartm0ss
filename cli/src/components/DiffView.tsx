import React from 'react';
import { Box, Text } from 'ink';

interface DiffViewProps {
  diff: string;
}

/**
 * Renders unified diffs with color coding
 */
export const DiffView: React.FC<DiffViewProps> = ({ diff }) => {
  if (!diff) return null;

  const lines = diff.split('\n');

  return (
    <Box flexDirection="column">
      {lines.map((line, i) => {
        if (line.startsWith('+')) {
          return (
            <Text key={i} color="green">
              {line}
            </Text>
          );
        } else if (line.startsWith('-')) {
          return (
            <Text key={i} color="red">
              {line}
            </Text>
          );
        } else {
          return <Text key={i}>{line}</Text>;
        }
      })}
    </Box>
  );
};

export default DiffView;