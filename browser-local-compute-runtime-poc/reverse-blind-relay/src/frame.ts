const DATA_FRAME_TYPE = 1;
const DATA_FRAME_HEADER_BYTES = 5;

export interface DataFrame {
  streamId: number;
  payload: Buffer;
}

export function encodeDataFrame(streamId: number, payload: Buffer): Buffer {
  const frame = Buffer.allocUnsafe(DATA_FRAME_HEADER_BYTES + payload.length);
  frame.writeUInt8(DATA_FRAME_TYPE, 0);
  frame.writeUInt32BE(streamId, 1);
  payload.copy(frame, DATA_FRAME_HEADER_BYTES);
  return frame;
}

export function decodeDataFrame(data: Buffer): DataFrame | null {
  if (data.length < DATA_FRAME_HEADER_BYTES) {
    return null;
  }

  const type = data.readUInt8(0);
  if (type !== DATA_FRAME_TYPE) {
    return null;
  }

  return {
    streamId: data.readUInt32BE(1),
    payload: data.subarray(DATA_FRAME_HEADER_BYTES),
  };
}
