const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }
  return data;
}

export function evaluateAssessment(payload) {
  return request("/evaluate/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function askTutor(payload) {
  return request("/ask/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchStudentGrowth(studentId) {
  return request(`/students/${encodeURIComponent(studentId)}/growth/`);
}
