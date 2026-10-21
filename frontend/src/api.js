const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');
const ACCESS_TOKEN_KEY = 'ticketly_access_token';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getAccessToken();
  if (token) headers.set('Authorization', 'Bearer ' + token);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new ApiError(
      typeof body === 'object' && body?.message ? body.message : 'Something went wrong. Please try again.',
      response.status,
    );
  }

  return body;
}

export function getAccessToken() {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function saveAccessToken(token) {
  if (token) window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export async function registerUser({ firstName, lastName, email, password }) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ first_name: firstName, last_name: lastName, email, password }),
  });
}

export async function loginUser(email, password) {
  const response = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  saveAccessToken(response?.data?.authorization?.access_token);
  return response;
}

export async function getCurrentUser() {
  return request('/api/auth/me');
}

export async function refreshAccessToken() {
  const response = await request('/api/auth/refresh', { method: 'POST' });
  saveAccessToken(response?.data?.authorization?.access_token);
  return response;
}

export async function logoutUser() {
  try {
    return await request('/api/auth/logout', { method: 'POST' });
  } finally {
    clearAccessToken();
  }
}

export async function updateCurrentUser(fields) {
  return request('/api/auth/me', { method: 'PATCH', body: JSON.stringify(fields) });
}

export async function changePassword(currentPassword, newPassword) {
  return request('/api/auth/change-password', {
    method: 'PATCH',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export async function forgotPassword(email) {
  return request('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}
