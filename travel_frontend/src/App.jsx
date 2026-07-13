import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './styles/index.css';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PreferencesPage from './pages/PreferencesPage';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import DestinationDetailPage from './pages/DestinationDetailPage';
import PackageDetail from './pages/PackageDetail';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Routes */}
            <Route
              path="/preferences"
              element={
                <ProtectedRoute>
                  <PreferencesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/destination/:destinationId"
              element={
                <ProtectedRoute>
                  <DestinationDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/package/:id"
              element={
                <ProtectedRoute>
                  <PackageDetail />
                </ProtectedRoute>
              }
            />

            {/* Redirect root to login or home */}
            <Route path="/" element={<Navigate to="/login" replace />} />

            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
