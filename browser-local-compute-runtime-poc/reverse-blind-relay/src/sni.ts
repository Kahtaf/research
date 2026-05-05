const TLS_HANDSHAKE = 0x16;
const TLS_CLIENT_HELLO = 0x01;
const EXT_SERVER_NAME = 0x0000;

function readUInt24BE(buffer: Buffer, offset: number): number {
  return (buffer[offset] << 16) | (buffer[offset + 1] << 8) | buffer[offset + 2];
}

function readVectorLength(buffer: Buffer, offset: number, bytes: 1 | 2): number {
  return bytes === 1 ? buffer.readUInt8(offset) : buffer.readUInt16BE(offset);
}

export function parseSniFromClientHello(buffer: Buffer): string | null {
  if (buffer.length < 5 || buffer.readUInt8(0) !== TLS_HANDSHAKE) {
    return null;
  }

  const recordLength = buffer.readUInt16BE(3);
  if (buffer.length < 5 + recordLength || buffer.readUInt8(5) !== TLS_CLIENT_HELLO) {
    return null;
  }

  const handshakeLength = readUInt24BE(buffer, 6);
  const handshakeEnd = Math.min(9 + handshakeLength, 5 + recordLength);
  let offset = 9;

  offset += 2; // client_version
  offset += 32; // random
  if (offset + 1 > handshakeEnd) return null;

  const sessionIdLength = readVectorLength(buffer, offset, 1);
  offset += 1 + sessionIdLength;
  if (offset + 2 > handshakeEnd) return null;

  const cipherSuitesLength = readVectorLength(buffer, offset, 2);
  offset += 2 + cipherSuitesLength;
  if (offset + 1 > handshakeEnd) return null;

  const compressionMethodsLength = readVectorLength(buffer, offset, 1);
  offset += 1 + compressionMethodsLength;
  if (offset + 2 > handshakeEnd) return null;

  const extensionsLength = readVectorLength(buffer, offset, 2);
  offset += 2;
  const extensionsEnd = Math.min(offset + extensionsLength, handshakeEnd);

  while (offset + 4 <= extensionsEnd) {
    const extensionType = buffer.readUInt16BE(offset);
    const extensionLength = buffer.readUInt16BE(offset + 2);
    offset += 4;

    if (offset + extensionLength > extensionsEnd) {
      return null;
    }

    if (extensionType === EXT_SERVER_NAME) {
      return parseServerNameExtension(buffer.subarray(offset, offset + extensionLength));
    }

    offset += extensionLength;
  }

  return null;
}

function parseServerNameExtension(extension: Buffer): string | null {
  if (extension.length < 2) {
    return null;
  }

  let offset = 2;
  const listEnd = Math.min(2 + extension.readUInt16BE(0), extension.length);

  while (offset + 3 <= listEnd) {
    const nameType = extension.readUInt8(offset);
    const nameLength = extension.readUInt16BE(offset + 1);
    offset += 3;

    if (offset + nameLength > listEnd) {
      return null;
    }

    if (nameType === 0) {
      return extension.subarray(offset, offset + nameLength).toString("utf8").toLowerCase();
    }

    offset += nameLength;
  }

  return null;
}

export function sessionIdFromSni(sni: string, suffix: string): string {
  const normalizedSni = sni.toLowerCase();
  const normalizedSuffix = suffix.trim().toLowerCase();

  if (!normalizedSuffix) {
    return normalizedSni;
  }

  const dotSuffix = normalizedSuffix.startsWith(".")
    ? normalizedSuffix
    : `.${normalizedSuffix}`;

  if (!normalizedSni.endsWith(dotSuffix)) {
    return "";
  }

  const withoutSuffix = normalizedSni.slice(0, -dotSuffix.length);
  return withoutSuffix.split(".").pop() ?? "";
}
