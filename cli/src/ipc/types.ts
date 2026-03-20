/**
 * Shared RPC message type definitions
 */

export interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

export interface JsonRpcResponse {
  jsonrpc: '2.0';
  id: number | string;
  result?: unknown;
  error?: JsonRpcError;
}

export interface JsonRpcNotification {
  jsonrpc: '2.0';
  method: string;
  params?: Record<string, unknown>;
}

export interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

/**
 * Loop event types streamed from orchestrator
 */
export type LoopEventType =
  | 'THOUGHT'
  | 'COMMAND'
  | 'TOOL_RESULT'
  | 'ANSWER'
  | 'ERROR'
  | 'LOOP_LIMIT';

export interface LoopEvent {
  type: LoopEventType;
  content: string;
  timestamp: string;
}

export interface TaskRunParams {
  goal: string;
  nonInteractive?: boolean;
}

export interface TaskCancelParams {
  taskId?: string;
}

export interface ConfigGetResult {
  rootModel: string;
  subagentModel: string;
  contextLimit: number;
}

export interface ConfigSetParams {
  rootModel?: string;
  subagentModel?: string;
  contextLimit?: number;
}