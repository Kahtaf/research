type BrowserPodStartOptions = {
  apiKey: string;
  token: string;
  sessionId: string;
  terminal: HTMLElement;
  onLog: (line: string) => void;
  onPortal: (url: string) => void;
};

async function copyBinaryFile(pod: any, sourcePath: string, targetPath: string) {
  const file = await pod.createFile(targetPath, "binary");
  const response = await fetch(sourcePath);
  if (!response.ok) {
    throw new Error(`failed to fetch ${sourcePath}: ${response.status}`);
  }
  await file.write(await response.arrayBuffer());
  await file.close();
}

async function writeTextFile(pod: any, path: string, text: string) {
  const file = await pod.createFile(path, "utf-8");
  await file.write(text);
  await file.close();
}

export async function startBrowserPod(options: BrowserPodStartOptions) {
  const { BrowserPod } = await import("@leaningtech/browserpod");
  options.onLog("booting BrowserPod");

  const pod = await BrowserPod.boot({ apiKey: options.apiKey });
  const terminal = await pod.createDefaultTerminal(options.terminal);

  pod.onPortal(({ url, port }: { url: string; port: number }) => {
    options.onLog(`portal ready on internal port ${port}: ${url}`);
    options.onPortal(new URL("/api/process?input=hello", url).toString());
  });

  try {
    await pod.createDirectory("/project");
  } catch {
    options.onLog("/project already exists");
  }

  await copyBinaryFile(
    pod,
    "/browserpod-project/package.json",
    "/project/package.json",
  );
  await copyBinaryFile(
    pod,
    "/browserpod-project/server.mjs",
    "/project/server.mjs",
  );
  await writeTextFile(
    pod,
    "/project/config.json",
    JSON.stringify(
      {
        token: options.token,
        sessionId: options.sessionId,
      },
      null,
      2,
    ),
  );

  options.onLog("installing BrowserPod inner npm dependencies");
  await pod.run("npm", ["install"], {
    echo: true,
    terminal,
    cwd: "/project",
  });

  options.onLog("starting BrowserPod API server");
  await pod.run("node", ["server.mjs"], {
    echo: true,
    terminal,
    cwd: "/project",
  });

  return pod;
}
