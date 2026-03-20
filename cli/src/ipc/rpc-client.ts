import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

/**
 * JSON-RPC 2.0 client over stdin/stdout
 * Handles message serialization, streaming event parsing, and error recovery
 */
export class RpcClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private buffer: string = '';
  private requestId: number = 0;

  /**
   * Spawn the Python orchestrator and establish IPC connection
   */
  start(orchestratorPath: string): void {
    this.process = spawn('python', [orchestratorPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.process.stdout?.on('data', (data: Buffer) => {
      this.handleData(data.toString());
    });

    this.process.stderr?.on('data', (data: Buffer) => {
      this.emit('error', new Error(data.toString()));
    });

    this.process.on('close', (code) => {
      this.emit('close', code);
    });
  }

  /**
   * Send a JSON-RPC request
   */
  call(method: string, params: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      if (!this.process?.stdin) {
        reject(new Error('Orchestrator process not running'));
        return;
      }

      const id = ++this.requestId;
      const request = JSON.stringify({
        jsonrpc: '2.0',
        id,
        method,
        params,
      });

      this.process.stdin.write(request + '\n');

      // TODO: Implement response handling with ID matching
      resolve(undefined);
    });
  }

  /**
   * Handle incoming data from orchestrator stdout
   */
  private handleData(data: string): void {
    this.buffer += data;
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.trim()) {
        try {
          const message = JSON.parse(line);
          this.emit('message', message);
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }

  /**
   * Clean shutdown of the orchestrator process
   */
  stop(): void {
    this.process?.kill('SIGTERM');
    this.process = null;
  }
}

export default RpcClient;