export function getCsrfToken() {
  const field = document.querySelector('[name=csrfmiddlewaretoken]');
  if (field?.value) return field.value;
  const cookie = document.cookie.split(';').map(s => s.trim()).find(s => s.startsWith('csrftoken='));
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : '';
}
export async function apiFetch(url, options = {}) {
  const target = new URL(url, window.location.href);
  if (target.origin !== window.location.origin) throw new Error('Only same-origin URLs are supported');
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method) && !headers.has('X-CSRFToken')) {
    const token = getCsrfToken();
    if (!token) throw new Error('CSRF token missing; include {% csrf_token %} in the page');
    headers.set('X-CSRFToken', token);
  }
  const response = await fetch(target, {...options, method, headers, credentials: 'same-origin', redirect: 'error'});
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  if (response.status === 204) return null;
  return response.headers.get('content-type')?.includes('application/json') ? response.json() : response.text();
}
export function setLoading(button, loading) { button.disabled = loading; button.setAttribute('aria-busy', String(loading)); }
export function showStatus(element, message) { element.textContent = message; }
export function confirmAction(message) { return window.confirm(message); }
