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
steps = '''<details><summary>Setup steps (about 5 minutes)</summary><ol>
      <li>On the account you use for Classroom, open <a href="https://script.google.com/home/projects/create" target="_blank" rel="noopener">script.google.com</a> and make a new project.</li>
      <li>Delete what is there, then <button id="b-copy" style="padding:3px 9px;font-size:13px">Copy the script</button> and paste it in. Change <code>KEY</code> at the top to any password you like. <details><summary>Show the script</summary><textarea id="gs-view" rows="8" readonly style="font:12px/1.4 ui-monospace,monospace;margin-top:6px"></textarea></details></li>
      <li>Top right <b>Deploy → New deployment</b>. Type: <b>Web app</b>. Execute as: <b>Me</b>. Who has access: <b>Anyone</b>. Deploy, then approve the permissions (Advanced → Go to project if it warns you).</li>
      <li>Copy the Web app URL (ends in <code>/exec</code>) and paste it below with your key.</li>
    </ol>
    <p style="margin-top:10px">That is enough for due dates: the script reads the calendar each class makes for you. No "add a service" step.</p>
    <p><b>Optional, for Turned in / Late badges:</b> in the script editor open <b>Project Settings</b> (gear), tick <b>Show "appsscript.json" manifest file</b>, open that file, replace everything with <button id="b-copyman" style="padding:3px 9px;font-size:13px">Copy manifest</button>, save, then Deploy → Manage deployments → edit → New version → Deploy and approve the new permissions. If your school blocks the Classroom API the script just keeps using the calendars.</p>
    </details>'''
h = re.sub(r'<details><summary>Setup steps \(about 5 minutes\)</summary><ol>.*?</ol></details>', lambda m: steps, h, count=1, flags=re.S)

# 3. copy-manifest handler (idempotent)
if "b-copyman').onclick" not in h:
    anchor = "  $('#b-script').onclick=()=>{"
    handler = ("  const gman=document.getElementById('gsman').textContent.trim()+String.fromCharCode(10);\n"
               "  $('#b-copyman').onclick=async ev=>{ev.preventDefault(); try{await navigator.clipboard.writeText(gman); toast('Manifest copied. Paste it over appsscript.json.')}catch{ toast('Copy failed. The manifest is in the repo as apps-script/appsscript.json') }};\n")
    assert anchor in h
    h = h.replace(anchor, handler + anchor, 1)

# 4. carry source + show calendar mode in the status line
h = h.replace("return {fetchedAt:raw.fetchedAt||new Date().toISOString(),courses,items};",
              "return {fetchedAt:raw.fetchedAt||new Date().toISOString(),source:raw.source||'',courses,items};")
h = h.replace("${cfg.mode==='demo'?' · demo data':''}</div>",
              "${cfg.mode==='demo'?' · demo data':''}${data?.source==='calendar'?' · calendar mode, no turned-in status':''}</div>")
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
