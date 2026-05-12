import { readFile } from "node:fs/promises";
import path from "node:path";
import mysql from "mysql2/promise";

const databaseUrl = process.env.DATABASE_URL;
const socketPath = process.env.MYSQL_SOCKET_PATH;
const config = databaseUrl
  ? {
      uri: databaseUrl,
      multipleStatements: true,
      ssl:
        process.env.DB_SSL_REJECT_UNAUTHORIZED === "false"
          ? { rejectUnauthorized: false }
          : { rejectUnauthorized: true },
    }
  : {
      ...(socketPath
        ? { socketPath }
        : {
            host: process.env.MYSQL_HOST || "127.0.0.1",
            port: Number(process.env.MYSQL_PORT || 3306),
            ssl:
              process.env.DB_SSL_REJECT_UNAUTHORIZED === "false"
                ? undefined
                : { rejectUnauthorized: true },
          }),
      user: process.env.MYSQL_USERNAME || "root",
      password: process.env.MYSQL_PASSWORD || "opensigner",
      database: process.env.MYSQL_DATABASE || "opensigner_poc",
      multipleStatements: true,
    };

const sql = await readFile(
  path.join(process.cwd(), "migrations", "001_initial.sql"),
  "utf8",
);
const connection = await mysql.createConnection(config);
await connection.query(sql);
await connection.end();
console.log("Applied migrations/001_initial.sql");
