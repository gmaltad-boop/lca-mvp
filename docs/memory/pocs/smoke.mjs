
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
const t0 = Date.now();
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [new URL("./node_modules/@modelcontextprotocol/server-everything/dist/index.js", import.meta.url).pathname]
});
const client = new Client({ name: "drael-smoke", version: "0.1.0" }, { capabilities: {} });
try {
  await client.connect(transport);
  const sv = client.getServerVersion();
  console.log("CONNECT ok | server:", JSON.stringify(sv), "|", Date.now() - t0, "ms");
  console.log("PING:", await client.ping());
  const { tools } = await client.listTools();
  console.log("TOOLS(" + tools.length + "):", tools.map(t => t.name).join(", "));
  for (const t of tools.slice(0, 6)) console.log("  schema", t.name, ":", JSON.stringify(t.inputSchema).slice(0, 160));
  const payload = "V1-divergencia-2-linhas|V2-churn27-relato|V3-10x-custo|V4-subidocast-ne-G4|V5-atribuicao-contexto|V6-executor-nao-notion|V7-modelo-metadado|V8-minuto-verificavel";
  const echo = await client.callTool({ name: "echo", arguments: { message: payload } });
  console.log("ECHO in :", payload);
  console.log("ECHO out:", JSON.stringify(echo.content && echo.content[0] && echo.content[0].text));
  if (tools.some(t => t.name === "get-sum")) {
    try {
      const s1 = await client.callTool({ name: "get-sum", arguments: { a: 2, b: 3 } });
      console.log("SUM(2,3) ->", JSON.stringify(s1.content && s1.content[0] && s1.content[0].text));
    } catch (e) { console.log("SUM falhou com {a,b}:", String(e).slice(0, 120)); }
  }
  const res = await client.listResources();
  console.log("RESOURCES:", res.resources ? res.resources.length : 0);
  await client.close();
  console.log("CLOSE ok | total", Date.now() - t0, "ms | VEREDITO: PASS-MCP-SMOKE");
} catch (e) {
  console.log("FAIL:", String(e).slice(0, 500));
  process.exitCode = 2;
}
