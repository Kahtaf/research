type HistoryEntry = {
  input: string;
  result: string;
  at: string;
};

export type BrowserState = {
  requestCount: number;
  history: HistoryEntry[];
};

const DB_NAME = "browser-local-api-state";
const STORE_NAME = "kv";
const STATE_KEY = "state";

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

export async function readState(): Promise<BrowserState> {
  const state = await runTransaction<BrowserState | undefined>("readonly", (store) =>
    store.get(STATE_KEY),
  );

  return state ?? { requestCount: 0, history: [] };
}

export async function recordRequest(
  input: string,
  result: string,
  at: string,
): Promise<BrowserState> {
  const current = await readState();
  const next = {
    requestCount: current.requestCount + 1,
    history: [{ input, result, at }, ...current.history].slice(0, 20),
  };

  await runTransaction<IDBValidKey>("readwrite", (store) =>
    store.put(next, STATE_KEY),
  );

  return next;
}
