self.importScripts("https://cdn.jsdelivr.net/pyodide/v0.21.3/full/pyodide.js");

let pyodideReadyPromise = loadPyodide();

self.onmessage = async (event) => {
  await pyodideReadyPromise;
  const { python } = event.data;
  try {
    let result = await self.pyodide.runPythonAsync(python);
    self.postMessage(result);
  } catch (err) {
    self.postMessage(err.toString());
  }
};
