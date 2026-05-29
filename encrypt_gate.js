// Encrypt a full HTML file with a password into a self-contained password-gated page.
// Usage: node encrypt_gate.js <input.html> <password> <output.html>
// Uses Web Crypto (PBKDF2-SHA256 -> AES-GCM). Decryption happens in the browser.
const fs = require('fs');
const { webcrypto } = require('crypto');
const { subtle } = webcrypto;

const [,, inPath, password, outPath] = process.argv;
if (!inPath || !password || !outPath) {
  console.error('Usage: node encrypt_gate.js <input.html> <password> <output.html>');
  process.exit(1);
}

const ITER = 250000;

(async () => {
  const plaintext = fs.readFileSync(inPath, 'utf8');
  const enc = new TextEncoder();
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
  const iv = webcrypto.getRandomValues(new Uint8Array(12));
  const keyMaterial = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  const key = await subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: ITER, hash: 'SHA-256' },
    keyMaterial, { name: 'AES-GCM', length: 256 }, false, ['encrypt']
  );
  const ctBuf = await subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(plaintext));
  const b64 = (u8) => Buffer.from(u8).toString('base64');
  const payload = {
    salt: b64(salt), iv: b64(iv), iter: ITER,
    ct: Buffer.from(ctBuf).toString('base64'),
  };

  const gate = `<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Mieszkania — dostęp</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0f1115;color:#e8ebf0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
  .box{background:#181b22;border:1px solid #262b35;border-radius:14px;padding:32px;width:320px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,.4)}
  h1{font-size:18px;margin:0 0 6px}
  p{color:#8b93a3;font-size:13px;margin:0 0 18px}
  input{width:100%;box-sizing:border-box;padding:11px 12px;border-radius:9px;border:1px solid #2b3140;background:#0f1115;color:#e8ebf0;font-size:15px;margin-bottom:12px}
  button{width:100%;padding:11px;border:0;border-radius:9px;background:#7aa2ff;color:#0f1115;font-weight:700;font-size:15px;cursor:pointer}
  button:hover{background:#9cb8ff}
  .err{color:#ff6b6b;font-size:13px;margin-top:10px;min-height:18px}
</style>
</head>
<body>
<div class="box">
  <h1>🔒 Mieszkania na wynajem</h1>
  <p>Wpisz hasło, żeby zobaczyć zestawienie.</p>
  <input type="password" id="pw" placeholder="hasło" autocomplete="current-password" autofocus>
  <button id="go">Pokaż</button>
  <div class="err" id="err"></div>
</div>
<script>
const DATA = ${JSON.stringify(payload)};
const b64d = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
async function unlock(){
  const pw = document.getElementById('pw').value;
  const err = document.getElementById('err'); err.textContent='';
  try{
    const enc = new TextEncoder();
    const km = await crypto.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveKey']);
    const key = await crypto.subtle.deriveKey(
      {name:'PBKDF2', salt:b64d(DATA.salt), iterations:DATA.iter, hash:'SHA-256'},
      km, {name:'AES-GCM', length:256}, false, ['decrypt']);
    const pt = await crypto.subtle.decrypt({name:'AES-GCM', iv:b64d(DATA.iv)}, key, b64d(DATA.ct));
    const html = new TextDecoder().decode(pt);
    document.open(); document.write(html); document.close();
  }catch(e){ err.textContent='Nieprawidłowe hasło.'; }
}
document.getElementById('go').addEventListener('click', unlock);
document.getElementById('pw').addEventListener('keydown', e => { if(e.key==='Enter') unlock(); });
</script>
</body>
</html>`;
  fs.writeFileSync(outPath, gate);
  console.log('Wrote', outPath, '(' + (gate.length/1024).toFixed(0) + ' KB, ' + ITER + ' PBKDF2 iters)');
})();
