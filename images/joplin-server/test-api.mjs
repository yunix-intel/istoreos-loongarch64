const BASE = 'http://127.0.0.1:22300';
const OLD_ADMIN_PASSWORD = 'JoplinTest123!';
const NEW_ADMIN_PASSWORD = 'AdminChanged456!';
const USER_PASSWORD = 'NormalUser789!';
const USER_EMAIL = 'syncuser@example.com';

const png = Buffer.from(
	'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
	'base64',
);

function log(...args) { console.log(...args); }

async function api(method, path, { session, json, form } = {}) {
	const headers = {};
	if (session) headers['X-Api-Auth'] = session;
	if (json !== undefined) headers['Content-Type'] = 'application/json';
	const res = await fetch(`${BASE}${path.startsWith('/') ? path : `/${path}`}`, {
		method,
		headers,
		body: json !== undefined ? JSON.stringify(json) : form,
	});
	const text = await res.text();
	let body = text;
	try { body = JSON.parse(text); } catch {}
	return { status: res.status, body, text, headers: res.headers };
}

function noteBody({ id, title, body }) {
	return `${title}

${body}

id: ${id}
parent_id: 000000000000000000000000000000F1
created_time: 2026-10-25T14:00:00.000Z
updated_time: 2026-10-25T14:00:00.000Z
is_conflict: 0
latitude: 0.00000000
longitude: 0.00000000
altitude: 0.0000
author:
source_url:
is_todo: 0
todo_due: 0
todo_completed: 0
source: joplindev-desktop
source_application: net.cozic.joplindev-desktop
application_data:
order: 0
user_created_time: 2026-10-25T14:00:00.000Z
user_updated_time: 2026-10-25T14:00:00.000Z
encryption_cipher_text:
encryption_applied: 0
markup_language: 1
is_shared: 1
share_id:
conflict_original_id:
master_key_id:
user_data:
deleted_time: 0
is_locked: 0
extracted_resource_ids:
type_: 1`;
}

function resourceBody({ id, title, mime, ext, size }) {
	return `${title}

id: ${id}
mime: ${mime}
filename:
created_time: 2026-10-25T14:00:00.000Z
updated_time: 2026-10-25T14:00:00.000Z
user_created_time: 2026-10-25T14:00:00.000Z
user_updated_time: 2026-10-25T14:00:00.000Z
file_extension: ${ext}
encryption_cipher_text:
encryption_applied: 0
encryption_blob_encrypted: 0
size: ${size}
share_id:
is_shared: 0
is_locked: 0
type_: 4`;
}

async function putFile(session, path, content, filename) {
	const form = new FormData();
	form.append('file', new Blob([content]), filename);
	return api('PUT', path, { session, form });
}

function assert(cond, message) {
	if (!cond) throw new Error(`ASSERT: ${message}`);
}

async function main() {
	// 1. admin login with DEFAULT_ADMIN_PASSWORD
	let r = await api('POST', '/api/sessions', {
		json: { email: 'admin@localhost', password: OLD_ADMIN_PASSWORD, platform: 2, version: '3.7.21' },
	});
	assert(r.status === 200 && r.body.id, `admin login failed: ${r.status} ${r.text}`);
	let adminSession = r.body.id;
	let adminId = r.body.user_id;
	log('PASS admin login, user_id=', adminId);

	// 2. admin user list
	r = await api('GET', '/api/users', { session: adminSession });
	assert(r.status === 200 && Array.isArray(r.body.items), `users list failed: ${r.status} ${r.text}`);
	log('PASS users list, count=', r.body.items.length);

	// 3. change admin password
	r = await api('PATCH', `/api/users/${adminId}`, { session: adminSession, json: { password: NEW_ADMIN_PASSWORD } });
	assert(r.status === 204 || r.status === 200, `admin password change failed: ${r.status} ${r.text}`);
	log('PASS admin password change', r.status);

	// old password must fail
	r = await api('POST', '/api/sessions', { json: { email: 'admin@localhost', password: OLD_ADMIN_PASSWORD } });
	assert(r.status === 403, `old admin password should fail, got ${r.status}`);
	log('PASS old admin password rejected', r.status);

	// new password works
	r = await api('POST', '/api/sessions', { json: { email: 'admin@localhost', password: NEW_ADMIN_PASSWORD } });
	assert(r.status === 200 && r.body.id, `admin login with new password failed: ${r.status} ${r.text}`);
	adminSession = r.body.id;
	log('PASS admin login with new password');

	// 4. create a normal user and set its password
	r = await api('POST', '/api/users', {
		session: adminSession,
		json: { email: USER_EMAIL, full_name: 'Sync Test User' },
	});
	assert(r.status === 200 && r.body.id, `create user failed: ${r.status} ${r.text}`);
	const userId = r.body.id;
	log('PASS create normal user', userId);

	r = await api('PATCH', `/api/users/${userId}`, {
		session: adminSession,
		json: { password: USER_PASSWORD, must_set_password: 0, email_confirmed: 1 },
	});
	assert(r.status === 204 || r.status === 200, `set user password failed: ${r.status} ${r.text}`);

	r = await api('POST', '/api/sessions', { json: { email: USER_EMAIL, password: USER_PASSWORD } });
	assert(r.status === 200 && r.body.id, `normal user login failed: ${r.status} ${r.text}`);
	const userSession = r.body.id;
	log('PASS normal user login');

	// 5. upload note + resource metadata + resource blob as the normal user
	const noteId = 'a1b2c3d4e5f60718293a4b5c6d7e8f90';
	const resourceId = 'b1c2d3e4f5061728394a5b6c7d8e9f01';
	const noteTitle = 'Loong64 Joplin Attachment Test';
	const noteText = 'This note was created through the Joplin Server API on loong64.';
	const note = noteBody({ id: noteId, title: noteTitle, body: `![my image](:/${resourceId})` });

	r = await putFile(userSession, `/api/items/root:/${noteId}.md:/content`, note, `${noteId}.md`);
	assert(r.status === 200 && r.body.id, `create note failed: ${r.status} ${r.text}`);
	log('PASS create note item', r.body.id, r.body.name);

	const resMeta = resourceBody({ id: resourceId, title: 'my image', mime: 'image/png', ext: 'png', size: png.length });
	r = await putFile(userSession, `/api/items/root:/${resourceId}.md:/content`, resMeta, `${resourceId}.md`);
	assert(r.status === 200 && r.body.id, `create resource metadata failed: ${r.status} ${r.text}`);
	log('PASS create resource metadata', r.body.name);

	r = await putFile(userSession, `/api/items/root:/.resource/${resourceId}:/content`, png, resourceId);
	assert(r.status === 200, `create resource blob failed: ${r.status} ${r.text}`);
	log('PASS upload resource blob, bytes=', png.length);

	// read back note content
	r = await api('GET', `/api/items/root:/${noteId}.md:/content`, { session: userSession });
	assert(r.status === 200 && r.text.includes(noteTitle), `read note failed: ${r.status}`);
	log('PASS read note content');

	// 6. share the note
	r = await api('POST', '/api/shares', { session: userSession, json: { type: 1, note_id: noteId } });
	assert(r.status === 200 && r.body.id, `share note failed: ${r.status} ${r.text}`);
	const shareId = r.body.id;
	log('PASS share note, share_id=', shareId);

	// 7. public share page + resource
	r = await api('GET', `/shares/${shareId}`);
	assert(r.status === 200 && r.text.includes(noteTitle), `share page failed: ${r.status}`);
	assert(r.text.includes('data-resource-id="' + resourceId + '"'), 'share page missing image tag');
	assert(/<img[^>]+src="[^"]+resource_id=/.test(r.text), 'share page image src missing');
	log('PASS share page renders note and image tag, length=', r.text.length);

	const imgRes = await fetch(`${BASE}/shares/${shareId}?resource_id=${resourceId}&t=1`);
	const imgBytes = Buffer.from(await imgRes.arrayBuffer());
	assert(imgRes.status === 200, `share resource failed: ${imgRes.status}`);
	assert(imgBytes.equals(png), `share resource bytes differ: ${imgBytes.length} vs ${png.length}`);
	log('PASS share page serves attached image bytes', imgBytes.length);

	// 8. verify item listing via delta (sync path)
	r = await api('GET', '/api/items/root/delta?limit=100', { session: userSession });
	assert(r.status === 200 && Array.isArray(r.body.items), `delta failed: ${r.status} ${r.text}`);
	log('PASS sync delta, items=', r.body.items.length);

	console.log(JSON.stringify({ adminId, userId, noteId, resourceId, shareId, imageBytes: png.length }));
}

main().catch((e) => { console.error('FAIL', e.stack || e); process.exit(1); });
