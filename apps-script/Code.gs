/**
 * Classroom Due bridge
 * 1. Paste this into a new project at script.google.com (use the account you use for Classroom).
 * 2. Change KEY below to any password you like.
 * 3. Services (+) -> Google Classroom API -> Add.
 * 4. Deploy -> New deployment -> Web app. Execute as: Me. Who has access: Anyone. Deploy and approve.
 * 5. Paste the Web app URL and the key into the Classroom Due app.
 */
var KEY = 'change-me';   // <- pick your own
var DAYS_BACK = 45;      // how far back to include old assignments

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (KEY && p.key !== KEY) return out({ error: 'Wrong key. Add ?key=YOURKEY or fix the key in the app.' });
  try { return out(collect()); }
  catch (err) { return out({ error: 'Script error: ' + (err && err.message ? err.message : err) }); }
}

function collect() {
  var courses = [], token;
  do {
    var r = Classroom.Courses.list({ courseStates: ['ACTIVE'], studentId: 'me', pageSize: 100, pageToken: token });
    courses = courses.concat(r.courses || []);
    token = r.nextPageToken;
  } while (token);

  var cutoff = Date.now() - DAYS_BACK * 864e5;
  var work = [], subs = [];
  courses.forEach(function (c) {
    var t;
    do {
      var w = Classroom.Courses.CourseWork.list(c.id, { courseWorkStates: ['PUBLISHED'], orderBy: 'dueDate desc', pageSize: 100, pageToken: t });
      (w.courseWork || []).forEach(function (cw) { if (keep(cw, cutoff)) work.push(slimWork(cw)); });
      t = w.nextPageToken;
    } while (t);
    var s;
    do {
      var r2 = Classroom.Courses.CourseWork.StudentSubmissions.list(c.id, '-', { userId: 'me', pageSize: 100, pageToken: s });
      (r2.studentSubmissions || []).forEach(function (x) { subs.push({ courseWorkId: x.courseWorkId, state: x.state, late: !!x.late }); });
      s = r2.nextPageToken;
    } while (s);
  });

  return {
    fetchedAt: new Date().toISOString(),
    courses: courses.map(function (c) { return { id: c.id, name: c.name, section: c.section || '' }; }),
    work: work,
    subs: subs
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

function out(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
