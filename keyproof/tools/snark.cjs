// Load the browser build of snarkjs in Node (no npm needed).
const fs = require("fs"), vm = require("vm"), path = require("path");
const code = fs.readFileSync(path.join(__dirname, "..", "web", "zk", "snarkjs.min.js"), "utf8");
vm.runInThisContext(code);
module.exports = globalThis.snarkjs;
