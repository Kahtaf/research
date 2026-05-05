import type { WebSocket } from "ws";
import type { Socket } from "node:net";

export interface ControlMessage {
  type: string;
  streamId?: number;
  sessionId?: string;
  issueToken?: string;
  sni?: string;
  remoteAddress?: string;
  reason?: string;
}

export interface BrowserSession {
  sessionId: string;
  socket: WebSocket;
  streams: Map<number, Socket>;
  connectedAt: number;
  issueToken: string;
}
