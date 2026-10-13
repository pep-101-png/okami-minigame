// Dependency-free launcher for the compiled, standalone download.
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const root = path.resolve(__dirname, "../dist");
const port = Number(process.env.PORT) || 5180;
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".json": "application/json",
};
if (!fs.existsSync(path.join(root, "index.html"))) {
  console.error(
    "Compiled game not found. Run npm ci and npm run build in the inkbound-2d folder.",
  );
  process.exit(1);
}
const server = http.createServer((req, res) => {
  let url;
  try {
    url = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
  } catch {
    res.writeHead(400);
    res.end("Invalid path");
    return;
  }
  let filename = path.resolve(root, "." + (url === "/" ? "/index.html" : url));
  if (filename !== root && !filename.startsWith(root + path.sep)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }
  fs.readFile(filename, (error, data) => {
    if (error) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    res.writeHead(200, {
      "Content-Type":
        mime[path.extname(filename)] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    res.end(data);
  });
});
server.on("error", (error) => {
  if (error.code === "EADDRINUSE")
    console.error(
      "Port " +
        port +
        " is already in use. Close the other 2D game window and try again.",
    );
  else console.error(error.message);
  process.exitCode = 1;
});
server.listen(port, "127.0.0.1", () => {
  const address = "http://localhost:" + port;
  console.log(
    "\nINKBOUND · The River Remembers\n" +
      address +
      "\nKeep this window open. Press Ctrl+C to stop.\n",
  );
  if (process.platform === "win32")
    spawn("cmd.exe", ["/c", "start", "", address], { stdio: "ignore" });
});
