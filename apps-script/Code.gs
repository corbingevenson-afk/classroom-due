/**
 * Classroom Due bridge
 * 1. Paste this into a new project at script.google.com (the account you use for Classroom).
 * 2. Change KEY below to any password you like.
 * 3. Project Settings (gear) -> tick "Show appsscript.json manifest file" -> open appsscript.json
 *    and replace it with the manifest from the app ("Copy manifest"). This is what lets the script read Classroom.
 * 4. Deploy -> New deployment -> Web app. Execute as: Me. Who has access: Anyone. Deploy and approve.
 * 5. Paste the Web app URL and the key into the Classroom Due app.
 *
 * It reads the Classroom API directly (assignments + turned-in status). If your school refuses that,
 * it falls back to your Classroom calendars and tells the app why.
 */
var KEY = 'change-me';   // <- pick your own
var DAYS_BACK = 45;      // how far back to include old assignments
var DAYS_AHEAD = 120;    // how far ahead to look in calendars

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (KEY && p.key !== KEY) return out({ error: 'Wrong key. Add ?key=YOURKEY or fix the key in the app.' });
  try {
    var viaApi = tryClassroomApi();
    if (viaApi) return out(viaApi);
    var res = viaCalendar();
    res.apiNote = LAST_API_ERROR || 'Classroom API returned nothing';
    return out(res);
  } catch (err) {
    return out({ error: 'Script error: ' + (err && err.message ? err.message : err) });
  }
}

// ---------- A. Classroom REST API through the script's own token ----------
var LAST_API_ERROR = '';
function api(url) {
  var r;
  try {
    r = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
  } catch (e) { LAST_API_ERROR = 'fetch blocked: ' + e.message; return null; }
  if (r.getResponseCode() !== 200) {
    var msg = r.getContentText();
    try { msg = JSON.parse(msg).error.message || msg; } catch (e2) {}
    LAST_API_ERROR = 'HTTP ' + r.getResponseCode() + ': ' + String(msg).slice(0, 300);
    return null;
  }
  return JSON.parse(r.getContentText());
}
function apiAll(url, key) {
  var items = [], token;
  do {
    var j = api(url + (token ? '&pageToken=' + token : ''));
    if (!j) return null;
    items = items.concat(j[key] || []);
    token = j.nextPageToken;
  } while (token);
  return items;
}
function tryClassroomApi() {
  var base = 'https://classroom.googleapis.com/v1/courses';
  var courses = apiAll(base + '?courseStates=ACTIVE&studentId=me&pageSize=100', 'courses');
  if (!courses) return null; // no permission -> fall back to calendars
  var cutoff = Date.now() - DAYS_BACK * 864e5;
  var work = [], subs = [];
  for (var i = 0; i < courses.length; i++) {
    var c = courses[i];
    var w = apiAll(base + '/' + c.id + '/courseWork?courseWorkStates=PUBLISHED&orderBy=dueDate%20desc&pageSize=100', 'courseWork') || [];
    for (var k = 0; k < w.length; k++) if (keep(w[k], cutoff)) work.push(slimWork(w[k]));
    var s = apiAll(base + '/' + c.id + '/courseWork/-/studentSubmissions?userId=me&pageSize=100', 'studentSubmissions') || [];
    for (var m = 0; m < s.length; m++) subs.push({ courseWorkId: s[m].courseWorkId, state: s[m].state, late: !!s[m].late });
  }
  return {
    fetchedAt: new Date().toISOString(), source: 'classroom',
    courses: courses.map(function (c) { return { id: c.id, name: c.name, section: c.section || '' }; }),
    work: work, subs: subs
  };
}
function keep(cw, cutoff) {
  if (cw.dueDate && cw.dueDate.year) {
    var d = cw.dueDate, t = cw.dueTime || { hours: 23, minutes: 59 };
    return Date.UTC(d.year, d.month - 1, d.day, t.hours || 0, t.minutes || 0) >= cutoff;
  }
  return Date.parse(cw.creationTime || 0) >= cutoff;
}
function slimWork(cw) {
  return {
    id: cw.id, courseId: cw.courseId, title: cw.title, description: (cw.description || '').slice(0, 160),
    dueDate: cw.dueDate || null, dueTime: cw.dueTime || null, maxPoints: cw.maxPoints || null,
    alternateLink: cw.alternateLink, workType: cw.workType, creationTime: cw.creationTime
  };
}

// ---------- B. Classroom calendars (built-in CalendarApp, always available) ----------
function viaCalendar() {
  var from = new Date(Date.now() - DAYS_BACK * 864e5), to = new Date(Date.now() + DAYS_AHEAD * 864e5);
  var cals = CalendarApp.getAllCalendars();
  var courses = [], work = [];
  for (var i = 0; i < cals.length; i++) {
    var cal = cals[i], id = cal.getId();
    if (id.indexOf('classroom') !== 0) continue;          // Classroom calendars are classroom…@group.calendar.google.com
    courses.push({ id: id, name: cal.getName(), section: '' });
    var evs = cal.getEvents(from, to);
    for (var k = 0; k < evs.length; k++) {
      var ev = evs[k], st = ev.getStartTime(), desc = ev.getDescription() || '';
      var link = (desc.match(/https?:\/\/classroom\.google\.com\/[^\s"<>]+/) || [''])[0];
      var item = {
        id: ev.getId(), courseId: id, title: ev.getTitle(),
        description: desc.replace(/<[^>]+>/g, ' ').replace(/https?:\/\/\S+/g, '').replace(/\s+/g, ' ').trim().slice(0, 160),
        alternateLink: link, workType: 'ASSIGNMENT', maxPoints: null, creationTime: ev.getDateCreated().toISOString()
      };
      if (ev.isAllDayEvent()) {
        var d = ev.getAllDayStartDate();
        item.dueDate = { year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() };
        item.dueTime = null;                                 // end of that day
      } else {
        item.dueDate = { year: st.getUTCFullYear(), month: st.getUTCMonth() + 1, day: st.getUTCDate() };
        item.dueTime = { hours: st.getUTCHours(), minutes: st.getUTCMinutes() };
      }
      work.push(item);
    }
  }
  if (!courses.length) return { fetchedAt: new Date().toISOString(), source: 'calendar', courses: [], work: [], subs: [] };
  return { fetchedAt: new Date().toISOString(), source: 'calendar', courses: courses, work: work, subs: [] };
}

function out(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
