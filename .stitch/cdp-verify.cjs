const fs = require('fs');
const port = process.argv[2];
const out = process.argv[3];
async function main() {
  const version = await fetch(`http://127.0.0.1:${port}/json/version`).then(r => r.json());
  const ws = new WebSocket(version.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const {resolve, reject} = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
    }
  };
  await new Promise(resolve => ws.onopen = resolve);
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const callId = ++id;
    pending.set(callId, {resolve, reject});
    ws.send(JSON.stringify({id: callId, method, params}));
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', {url: 'http://127.0.0.1:5173/'});
  await new Promise(resolve => setTimeout(resolve, 4500));
  const before = await send('Runtime.evaluate', {
    expression: `(() => {
      const el = document.getElementById('process');
      if (el) el.scrollIntoView({block: 'start'});
      return {hasProcess: !!el, scrollY, height: document.documentElement.scrollHeight};
    })()`,
    returnByValue: true
  });
  await new Promise(resolve => setTimeout(resolve, 800));
  const after = await send('Runtime.evaluate', {expression: `({scrollY, processTop: document.getElementById('process')?.getBoundingClientRect().top, hasText: document.body.innerText.includes('三个步骤')})`, returnByValue: true});
  const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false});
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log(JSON.stringify({before: before.result.value, after: after.result.value, out}, null, 2));
  ws.close();
}
main().catch(err => { console.error(err); process.exit(1); });
