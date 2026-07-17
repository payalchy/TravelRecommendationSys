import axios from 'axios';

// Vite environment variable support
const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ===============================
// REQUEST INTERCEPTOR
// Add JWT token automatically
// ===============================
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ===============================
// RESPONSE INTERCEPTOR
// Handle unauthorized responses
// ===============================
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized - Token may be invalid');

      // Optional auto logout
      localStorage.removeItem('access_token');
    }

    return Promise.reject(error);
  }
);

// ===============================
// AUTHENTICATION API
// ===============================
export const authAPI = {
  // Register user
  register: (data) =>
    api.post('/users/register/', data),

  // Login user
  login: (credentials) =>
    api.post('/token/', {
      username: credentials.username,
      password: credentials.password,
    }),

  // Logout
  logout: () => {
    localStorage.removeItem('access_token');
  },
};

// ===============================
// RECOMMENDATION API
// ===============================
export const recommendationAPI = {
  // ---------- USER PROFILE ----------

  // Get user profile
  getUserProfile: () =>
    api.get('/users/profile/'),

  // Update user profile
  updateUserProfile: (data) =>
    api.patch('/users/profile/', data),

  // Get available travel styles
  getTravelStyles: () =>
    api.get('/users/travel-styles/'),

  // Get user profile history
  getUserProfileHistory: () =>
    api.get('/users/profile/history/'),

  getUserSearchHistory: () =>
    api.get('/users/search-history/'),

  // Search destinations by name, city, or tags
  searchDestinations: (query, offset = 0, limit = 6) =>
    api.get('/destination/search/', {
      params: { q: query, offset, limit },
    }),

  // ---------- RECOMMENDATIONS ----------

  // Get destination recommendations
  getRecommendations: (payload) =>
    api.post('/recommend/', payload),

  // Get blended personalized suggestions
  getYouMightAlsoLike: (topN = 6) =>
    api.get('/recommend/you-might-also-like/', {
      params: { top_n: topN },
    }),

  // Get ranked package recommendations
  getRecommendedPackages: (payload) =>
    api.post('/recommend/available-packages/', payload),

  // Get a single recommended package by id
  getRecommendedPackage: (packageId) =>
    api.get(`/recommend/available-packages/${packageId}/`),

  // Create a booking request
  createBooking: (payload) =>
    api.post('/recommend/bookings/', payload),

  // Get the logged-in user's booking history
  getUserBookings: () =>
    api.get('/recommend/bookings/history/'),

  // Get provinces list
  getProvinces: () =>
    api.get('/destination/provinces/'),

  // ---------- DESTINATIONS ----------

  // Get packages for specific destination
  getDestinationPackages: (destinationId) =>
    api.get(`/destinations/${destinationId}/packages/`),

  // ---------- GEOCODING ----------

  // Geocode destination name
  geocodeDestination: (name) =>
    api.get('/destination/geocode/', {
      params: { name },
    }),
};

export default api;