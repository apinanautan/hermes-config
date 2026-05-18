const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function main() {
  const targetPageId = '357EB0543D7498C3B6B9673FB7C7184D';

  console.log('[1] Fetching CDP targets...');
  const targets = await fetchJson('http://localhost:9222/json');
  const target = targets.find(t => t.id === targetPageId);
  if (!target) { console.error('Target not found'); process.exit(1); }
  
  const wsUrl = target.webSocketDebuggerUrl;
  console.log('[2] WS URL:', wsUrl.substring(0, 50) + '...');
  
  const ws = new WebSocket(wsUrl);
  let msgId = 1;
  const pending = {};

  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = msgId++;
    pending[id] = (msg) => {
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg);
    };
    ws.send(JSON.stringify({ id, method, params }));
  });

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.id && pending[msg.id]) {
      pending[msg.id](msg);
      delete pending[msg.id];
    } else if (msg.method) {
      console.log('[EVT]', msg.method);
    }
  });

  ws.on('open', async () => {
    console.log('[3] Connected');
    const startTime = Date.now();
    
    try {
      // Get buttons as JSON string
      console.log('[4] Getting buttons...');
      const r1 = await send('Runtime.evaluate', { expression: 'JSON.stringify(Array.from(document.querySelectorAll("button")).map(function(b){return b.textContent.trim();}))' });
      const buttonsJson = r1.result.result.value;
      console.log('[4b] Buttons:', buttonsJson);
      
      // Get button position as JSON string
      console.log('[5] Getting button position...');
      const r2 = await send('Runtime.evaluate', { expression: 'JSON.stringify((function(){var b=document.querySelector("button");if(!b)return null;var r=b.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,text:b.textContent.trim()};})())' });
      const posJson = r2.result.result.value;
      console.log('[5b] Pos JSON:', posJson);
      const pos = JSON.parse(posJson);
      
      console.log('[6] Button pos:', JSON.stringify(pos));
      
      // Zigzag gesture
      console.log('[7] Zigzag...');
      for (let i = 0; i < 15; i++) {
        await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pos.x + (i%2===0?-40:40), y: pos.y + i*4, button: 'none', clickCount: 0 });
      }
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pos.x, y: pos.y, button: 'none', clickCount: 0 });
      await new Promise(r => setTimeout(r, 100));
      
      // CLICK
      const clickTime = Date.now();
      console.log('[8] CLICK at', pos.x, pos.y);
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: pos.x, y: pos.y, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: pos.x, y: pos.y, button: 'left', clickCount: 1 });
      
      // IMMEDIATE screenshot
      console.log('[9] Screenshot...');
      const ssResult = await send('Page.captureScreenshot', { format: 'png' });
      const ssTime = Date.now();
      const ssBuf = Buffer.from(ssResult.result.data, 'base64');
      const ssPath = 'C:/Users/Apinan/owen-workspace/live_scan_click_screenshot.png';
      fs.writeFileSync(ssPath, ssBuf);
      console.log('[9b] Screenshot saved:', ssPath, ssBuf.length, 'bytes');
      
      // DOM snapshot
      console.log('[10] DOM snapshot...');
      const r3 = await send('Runtime.evaluate', { expression: 'document.documentElement.outerHTML' });
      const domText = r3.result.result.value;
      fs.writeFileSync('C:/Users/Apinan/owen-workspace/live_scan_dom.txt', domText, 'utf8');
      console.log('[10b] DOM saved, length:', domText.length);
      
      // Plain DOM structure as JSON string
      console.log('[11] Plain structure...');
      const r4 = await send('Runtime.evaluate', { expression: 'JSON.stringify((function(){var lines=[];var walk=function(el,d){if(el.nodeType===1){var s="  ".repeat(d)+"<"+el.tagName.toLowerCase();if(el.id)s+=" id="+el.id;var cls=el.className;if(cls&&typeof cls==="string"&&cls.trim())s+=" class="+cls.trim();var txt=el.childNodes.length===1&&el.childNodes[0].nodeType===3?el.childNodes[0].textContent.trim():"";if(txt)s+=">"+txt+"</"+el.tagName.toLowerCase()+">";else{s+=">";lines.push(s);el.childNodes.forEach(function(c){walk(c,d+1);});lines.push("  ".repeat(d)+"</"+el.tagName.toLowerCase()+">");}}else if(el.nodeType===3){var t=el.textContent.trim();if(t)lines.push("  ".repeat(d)+"TEXT:\""+t+"\"");}};walk(document.body,0);return lines.join("\\n");})())' });
      fs.writeFileSync('C:/Users/Apinan/owen-workspace/live_scan_dom_structure.txt', r4.result.result.value, 'utf8');
      
      console.log('\n========================================');
      console.log('RESULTS');
      console.log('========================================');
      console.log('Screenshot:', ssPath);
      console.log('Screenshot size:', ssBuf.length, 'bytes');
      console.log('Click-to-screenshot (ms):', ssTime - clickTime);
      console.log('Click timestamp (ms from start):', clickTime - startTime);
      console.log('Screenshot timestamp (ms from start):', ssTime - startTime);
      console.log('Button clicked:', pos.text);
      console.log('Buttons on page:', buttonsJson);
      console.log('DOM file: C:/Users/Apinan/owen-workspace/live_scan_dom.txt');
      console.log('Structure: C:/Users/Apinan/owen-workspace/live_scan_dom_structure.txt');
      console.log('========================================\n');
      
    } catch(e) {
      console.error('[!] Error:', e.message);
    }
    
    ws.close();
    process.exit(0);
  });

  ws.on('error', (e) => { console.error('[WS ERR]', e.message); process.exit(1); });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });