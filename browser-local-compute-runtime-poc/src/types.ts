export type RelayRequest = {
  type: "request";
  requestId: string;
  method: string;
  path: string;
  query: string;
  headers: Record<string, string>;
  body: string;
};

export type RelayResponse = {
  type: "response";
  requestId: string;
  status: number;
  headers: Record<string, string>;
  body: string;
};

export type RuntimeInitMessage = {
  type: "init";
  sessionId: string;
};

export type RuntimeRequestMessage = {
  type: "handle";
  request: RelayRequest;
};

export type RuntimeResponseMessage = {
  type: "handled";
  requestId: string;
  response: Omit<RelayResponse, "type" | "requestId">;
};

export type RuntimeErrorMessage = {
  type: "runtime-error";
  requestId?: string;
  message: string;
};

export type RuntimeMessage = RuntimeInitMessage | RuntimeRequestMessage;

export type RuntimeReply = RuntimeResponseMessage | RuntimeErrorMessage;
