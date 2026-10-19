"""Embed apps-script/Code.gs and appsscript.json into index.html, then rebuild artifact.html."""
import re, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
idx = root / 'index.html'
h = idx.read_text(encoding='utf-8')
gs = (root / 'apps-script' / 'Code.gs').read_text(encoding='utf-8')
man = (root / 'apps-script' / 'appsscript.json').read_text(encoding='utf-8')
assert '</script>' not in gs and '</script>' not in man

# 1. embedded script + manifest blocks
h = re.sub(r'<script type="text/plain" id="gs">.*?</script>\n(?:<script type="text/plain" id="gsman">.*?</script>\n)?',
           lambda m: '<script type="text/plain" id="gs">\n' + gs + '</script>\n<script type="text/plain" id="gsman">\n' + man + '</script>\n', h, count=1, flags=re.S)

# 2. setup steps
steps = '''<details open><summary>Setup steps, start to finish</summary>
    <p><b>Part 1: new project</b></p><ol>
      <li>On the account you use for Classroom, open <a href="https://script.google.com/home/projects/create" target="_blank" rel="noopener">script.google.com</a> and make a new project.</li>
      <li>Click inside <code>Code.gs</code>, Ctrl+A, Delete. Then <button id="b-copy" style="padding:3px 9px;font-size:13px">Copy the script</button>, go back, Ctrl+V, Ctrl+S. Near the top you should see <code>var VERSION</code>. <details><summary>Show the script</summary><textarea id="gs-view" rows="10" readonly style="font:12px/1.4 ui-monospace,monospace;margin-top:6px"></textarea></details></li>
      <li>Find <code>var KEY = 'change-me';</code> and change <code>change-me</code> to any password, keeping the quotes. Ctrl+S.</li>
    </ol>
    <p><b>Part 2: the manifest</b></p><ol start="4">
      <li>Left sidebar, gear icon (Project Settings). Tick <b>Show "appsscript.json" manifest file in editor</b>.</li>
      <li>Left sidebar, <code>&lt; &gt;</code> icon (Editor). In Files click <code>appsscript.json</code>. Click inside it, Ctrl+A, Delete so it is empty.</li>
      <li><button id="b-copyman" style="padding:3px 9px;font-size:13px">Copy manifest</button> then Ctrl+V, Ctrl+S. The file must be exactly these 11 lines:
<pre id="gsman-view" style="margin:8px 0 0;padding:10px 12px;background:var(--card2);border:1px solid var(--line);border-radius:10px;font:12px/1.5 ui-monospace,monospace;white-space:pre;overflow-x:auto;user-select:all"></pre></li>
    </ol>
    <p><b>Part 3: test the permission</b></p><ol start="7">
      <li>Click <code>Code.gs</code>. In the toolbar dropdown next to Run, pick <code>checkClassroom</code>. Click <b>Run</b>.</li>
      <li>Review permissions, pick the school account. If it says "Google hasn't verified this app": Advanced → Go to (project) → Allow.</li>
      <li>The Execution log at the bottom should say <b>CLASSROOM OK</b> with your classes. If it says CLASSROOM BLOCKED, send Claude that line.</li>
    </ol>
    <p><b>Part 4: publish</b></p><ol start="10">
      <li>Top right <b>Deploy → New deployment</b>. Gear next to "Select type" → <b>Web app</b>.</li>
      <li>Execute as: <b>Me</b>. Who has access: <b>Anyone</b>. Deploy. Copy the Web app URL (ends in <code>/exec</code>).</li>
      <li>Paste it below with your key and hit Save &amp; sync. The status line should say <b>bridge v5</b>.</li>
    </ol>
    <p>Changed the script later? <b>Deploy → Manage deployments → pencil → Version: New version → Deploy</b>, or the old copy keeps running.</p>
    </details>'''
h = re.sub(r'<details( open)?><summary>Setup steps[^<]*</summary>.*?</details>\s*(?=<label>Web app URL)', lambda m: steps, h, count=1, flags=re.S)

# 3. copy-manifest handler (idempotent)
h = re.sub(r"^  const gman=.*\n|^  \$\('#gsman-view'\)\.value=gman;\n|^  \$\('#b-copyman'\)\.onclick=.*\n", '', h, flags=re.M)
if True:
    anchor = "  $('#b-script').onclick=()=>{"
    handler = ("  const gman=document.getElementById('gsman').textContent.trim()+String.fromCharCode(10);\n"
               "  $('#gsman-view').textContent=gman;\n  $('#b-copyman').onclick=async ev=>{ev.preventDefault(); try{await navigator.clipboard.writeText(gman); toast('Manifest copied. Paste it over appsscript.json.')}catch{ const r=document.createRange(); r.selectNodeContents($('#gsman-view')); getSelection().removeAllRanges(); getSelection().addRange(r); toast('Press Ctrl+C to copy the selected manifest') }};\n")
    assert anchor in h
    h = h.replace(anchor, handler + anchor, 1)

# 4. carry source + show calendar mode in the status line
ret_new = "return {fetchedAt:raw.fetchedAt||new Date().toISOString(),source:raw.source||'',apiNote:raw.apiNote||'',version:raw.version||0,courses,items};"
h, n1 = re.subn(r"return \{fetchedAt:raw\.fetchedAt\|\|new Date\(\)\.toISOString\(\),[^\n]*?courses,items\};", lambda m: ret_new, h, count=1)
tail_new = ("${cfg.mode==='demo'?' · demo data':''}${data?.source==='calendar'?' · calendar mode':''}${data?.version?` · bridge v${data.version}`:' · OLD script, redeploy'}`:'Not synced yet'}</div>"
            "${data?.apiNote?`<div class=\"status err\" id=\"apinote\">Classroom API refused: ${esc(data.apiNote)} "
            "${/insufficient|scope/i.test(data.apiNote)?'Do step 3 (paste the manifest) and redeploy as a new version.'"
            ":/not been used|disabled|blocked|403/i.test(data.apiNote)?'Your school blocks the Classroom API for scripts. Tell Claude this message.':''}</div>`:''}")
h, n2 = re.subn(r"\$\{cfg\.mode==='demo'\?' · demo data':''\}[^\n]*", lambda m: tail_new, h, count=1)
assert n1 == 1 and n2 == 1, (n1, n2)
idx.write_text(h, encoding='utf-8')

# 5. artifact build
head = re.search(r'<head>(.*?)</head>', h, re.S).group(1)
body = re.search(r'<body>(.*?)</body>', h, re.S).group(1)
title = re.search(r'<title>.*?</title>', head).group(0)
style = re.search(r'<style>.*?</style>', head, re.S).group(0)
body = body.replace("if('serviceWorker' in navigator && location.protocol==='https:') navigator.serviceWorker.register('sw.js').catch(()=>{});", "")
body = body.replace('Could not reach the script (blocked or offline). Open Settings and use "Paste JSON" instead.',
                    'This copy of the app cannot fetch directly. Open Settings and use "Paste JSON" instead.')
style = style.replace('.wrap{max-width:720px;margin:0 auto;padding:16px 16px calc(32px + env(safe-area-inset-bottom))}',
                      '.wrap{max-width:720px;margin:0 auto;padding-block:16px 32px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}')
(root / 'artifact.html').write_text(title + '\n<meta name="claude:viewport-fit-sides" content="cover">\n' + style + body, encoding='utf-8')

# 6. syntax-check the page script
js = re.findall(r'<script>\n(.*?)</script>', h, re.S)[-1]
(root / '_c.js').write_text(js, encoding='utf-8')
print('embedded ok; gs blocks:', h.count('id="gs"'), h.count('id="gsman"'), '| b-copyman:', h.count('b-copyman'))
