const DB_NAME = "browser-local-mcp-text";
const STORE_NAME = "kv";
const TEXT_KEY = "sourceText";
const REQUEST_COUNT_KEY = "requestCount";

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function runTransaction<T>(
  mode: IDBTransactionMode,
  callback: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openDatabase().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, mode);
        const store = transaction.objectStore(STORE_NAME);
        const request = callback(store);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
        transaction.oncomplete = () => db.close();
        transaction.onerror = () => {
          db.close();
          reject(transaction.error);
        };
      }),
  );
}

export async function readText(): Promise<string | undefined> {
  return runTransaction<string | undefined>("readonly", (store) =>
    store.get(TEXT_KEY),
  );
}

export async function writeText(text: string): Promise<void> {
  await runTransaction<IDBValidKey>("readwrite", (store) =>
    store.put(text, TEXT_KEY),
  );
}

export async function readRequestCount(): Promise<number> {
  const count = await runTransaction<number | undefined>("readonly", (store) =>
    store.get(REQUEST_COUNT_KEY),
  );
  return count ?? 0;
}

export async function incrementRequestCount(): Promise<number> {
  const current = await readRequestCount();
  const next = current + 1;
  await runTransaction<IDBValidKey>("readwrite", (store) =>
    store.put(next, REQUEST_COUNT_KEY),
  );
  return next;
}
