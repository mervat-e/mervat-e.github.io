self.importScripts("https://cdn.jsdelivr.net/pyodide/v0.21.3/full/pyodide.js");

let pyodideReadyPromise = loadPyodide();

pyodideReadyPromise.then((pyodide) => {
  self.pyodide = pyodide;
});

self.onmessage = async (event) => {
  await pyodideReadyPromise;
  const { python } = event.data;

  try {
    let result = await self.pyodide.runPythonAsync(python);
    self.postMessage(result === undefined ? "✅ Code ran successfully." : result.toString());
  } catch (err) {
    self.postMessage("❌ Error: " + err.toString());
  }
};
