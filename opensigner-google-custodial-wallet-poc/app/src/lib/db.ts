import mysql, {
  type ExecuteValues,
  type ResultSetHeader,
  type RowDataPacket,
} from "mysql2/promise";

import { requiredEnv } from "./env";

let pool: mysql.Pool | undefined;

export function getPool(): mysql.Pool {
  if (pool) return pool;

  const databaseUrl = process.env.DATABASE_URL;
  const ssl =
    process.env.DB_SSL_REJECT_UNAUTHORIZED === "false"
      ? { rejectUnauthorized: false }
      : { rejectUnauthorized: true };

  if (databaseUrl) {
    pool = mysql.createPool({
      uri: databaseUrl,
      ssl,
      connectionLimit: Number(process.env.DB_CONNECTION_LIMIT || 5),
      namedPlaceholders: true,
    });
    return pool;
  }

  const socketPath = process.env.MYSQL_SOCKET_PATH;
  pool = mysql.createPool({
    ...(socketPath
      ? { socketPath }
      : {
          host: requiredEnv("MYSQL_HOST"),
          port: Number(process.env.MYSQL_PORT || 3306),
          ssl,
        }),
    user: requiredEnv("MYSQL_USERNAME"),
    password: requiredEnv("MYSQL_PASSWORD"),
    database: requiredEnv("MYSQL_DATABASE"),
    connectionLimit: Number(process.env.DB_CONNECTION_LIMIT || 5),
    namedPlaceholders: true,
  });
  return pool;
}

export async function rows<T extends RowDataPacket>(
  sql: string,
  params: ExecuteValues[] = [],
): Promise<T[]> {
  const [result] = await getPool().execute<T[]>(sql, params);
  return result;
}

export async function one<T extends RowDataPacket>(
  sql: string,
  params: ExecuteValues[] = [],
): Promise<T | null> {
  const result = await rows<T>(sql, params);
  return result[0] ?? null;
}

export async function exec(
  sql: string,
  params: ExecuteValues[] = [],
): Promise<ResultSetHeader> {
  const [result] = await getPool().execute<ResultSetHeader>(sql, params);
  return result;
}
