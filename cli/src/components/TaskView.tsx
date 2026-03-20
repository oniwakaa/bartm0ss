import React from 'react';
import { Box, Text } from 'ink';

interface TaskViewProps {
  thoughts: string[];
  commands: string[];
  toolResults: string[];
  answer?: string;
}

/**
 * Renders live-streaming THOUGHT / COMMAND / TOOL_RESULT / ANSWER events
 */
export const TaskView: React.FC<TaskViewProps> = ({
  thoughts,
  commands,
  toolResults,
  answer,
}) => {
  return (
    <Box flexDirection="column">
      {thoughts.map((t, i) => (
        <Text key={i} dimColor>
          💭 {t}
        </Text>
      ))}
      {commands.map((c, i) => (
        <Text key={i} color="cyan">
          ⚡ {c}
        </Text>
      ))}
      {toolResults.map((r, i) => (
        <Box key={i} flexDirection="column" borderStyle="round" borderColor="gray">
          <Text>{r}</Text>
        </Box>
      ))}
      {answer && (
        <Text color="green" bold>
          ✓ {answer}
        </Text>
      )}
    </Box>
  );
};

export default TaskView;