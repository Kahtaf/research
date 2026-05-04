import { handleRuntimeRequest } from "./runtime-handler";
import type { RuntimeMessage, RuntimeReply } from "./types";

let sessionId = "";
let encryptionPrivateKey: CryptoKey | undefined;

function reply(message: RuntimeReply) {
  self.postMessage(message);
}

self.onmessage = async (event: MessageEvent<RuntimeMessage>) => {
  const message = event.data;

  try {
    if (message.type === "init") {
      sessionId = message.sessionId;
      encryptionPrivateKey = message.encryptionPrivateKey;
      return;
    }

    if (!sessionId || !encryptionPrivateKey) {
      reply({
        type: "runtime-error",
        requestId: message.request.requestId,
        message: "runtime not initialized",
      });
      return;
    }

    const response = await handleRuntimeRequest(message.request, {
      sessionId,
      encryptionPrivateKey,
    });

    reply({
      type: "handled",
      requestId: message.request.requestId,
      response,
    });
  } catch (error) {
    reply({
      type: "runtime-error",
      requestId: message.type === "handle" ? message.request.requestId : undefined,
      message: error instanceof Error ? error.message : String(error),
    });
  }
};
