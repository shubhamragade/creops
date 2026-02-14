import axios from 'axios';

// Determine the API base URL
// Priority: env var > auto-detect production > localhost fallback
function getBaseURL(): string {
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
    }
    // Auto-detect: if running on Vercel production domain, use Render backend
    if (typeof window !== 'undefined' && window.location.hostname === 'creops.vercel.app') {
        return 'https://careops-backend-6img.onrender.com';
    }
    return 'http://localhost:8000';
}

const api = axios.create({
    baseURL: getBaseURL(),
    // Don't set default Content-Type - let each request specify its own
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle 401
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            // Redirect to login if unauthorized
            // Avoid redirect loops if already on login
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
