# Classroom Due

Your Google Classroom assignments in one clean list: overdue, today, tomorrow, this week, later. Shows points, turned-in status, and a link back to Classroom. Works as an installable app on a Chromebook.

Live app: https://classroom-due.lassroom-ue.workers.dev/ (Cloudflare). GitHub Pages mirror: https://corbingevenson-afk.github.io/classroom-due/

## Connect it to your Classroom (about 5 minutes)

Use the Google account you use for Classroom. No "add a service" step is needed: the script reads the calendar each class makes for you, and uses the full Classroom API only if your account is allowed to.

1. Open https://script.google.com/home/projects/create (new project).
2. Delete everything in the editor and paste in the script (use **Copy the script** inside the app, or [`apps-script/Code.gs`](apps-script/Code.gs)). Change `KEY` at the top to any password you like.
3. Top right: **Deploy -> New deployment**. Gear icon -> type **Web app**. Execute as: **Me**. Who has access: **Anyone**. Click **Deploy** and approve the permissions (Calendar + external connections). If Google shows a warning screen, click **Advanced -> Go to (project name)**.
4. Copy the **Web app URL** (ends in `/exec`). Open the app, paste the URL and your key, hit **Save & sync**.

Nobody else can see your assignments unless they have both the URL and your key.

### Optional: Turned in / Late badges

Calendar mode only knows due dates. To get submission status the script needs Classroom API permission. In the script editor open **Project Settings** (gear), tick **Show "appsscript.json" manifest file in editor**, open that file and replace it with [`apps-script/appsscript.json`](apps-script/appsscript.json) (or **Copy manifest** in the app). Save, then **Deploy -> Manage deployments -> edit -> New version -> Deploy** and approve the new permissions. If the school blocks the Classroom API, the script silently keeps using the calendars.

### If the sync fails

Some school accounts block "Anyone" web apps or block fetches from other sites. Open your Web app URL in a new tab with `?key=YOURKEY` on the end. If you see JSON text, select all, copy, and paste it into **Settings → Fetch blocked? Paste JSON instead**. If you see an error from Google instead, your school has turned off Apps Script and you will need the OAuth path or to ask IT.

### Advanced: OAuth client ID

Only if the bridge is blocked. Make a Google Cloud project, enable the Google Classroom API, set up an OAuth consent screen (External, Testing, add yourself as a test user), create an **OAuth client ID → Web application** with authorized JavaScript origin `https://corbingevenson-afk.github.io`, and paste the client ID into **Settings → Advanced**. Note that Google blocks unconfigured third-party apps for under-18 school accounts, so this often will not work with a school account.

## Install on a Chromebook

Open the live link in Chrome, click the install icon at the right end of the address bar (or menu → **Install Classroom Due**). It then opens from the launcher like a normal app and works offline with the last synced data.

## Redeploy

Cloudflare: `npx wrangler deploy` from this folder (needs `npx wrangler login` once). GitHub mirror: commit and `git push` to `main`.
