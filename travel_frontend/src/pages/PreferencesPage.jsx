import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import MapPicker from '../components/MapPicker';

export default function PreferencesPage() {
  const navigate = useNavigate();
  const { user, refreshUserProfile } = useAuth();
  const [formData, setFormData] = useState({
    budget: '',
    preferred_duration: '',
    preferred_season: 'spring',
    preferred_travel_style_ids: [],
  });
  const [travelStyles, setTravelStyles] = useState([]);
  const [provinces, setProvinces] = useState([]);
  const [selectedProvinces, setSelectedProvinces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [locationData, setLocationData] = useState({
    latitude: 27.7172,
    longitude: 85.324,
  });
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState('');

  const getStoredProvinceList = () => normalizeProvinceList(localStorage.getItem('preferred_provinces'));

  const normalizeProvinceList = (value) => {
    if (Array.isArray(value)) {
      return value.map((province) => String(province).trim()).filter(Boolean);
    }

    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) return [];

      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) {
          return parsed.map((province) => String(province).trim()).filter(Boolean);
        }
      } catch {
        return trimmed
          .split(',')
          .map((province) => String(province).trim())
          .filter(Boolean);
      }
    }

    return [];
  };

  const storeProvinceSelection = (provinces) => {
    localStorage.setItem('preferred_provinces', JSON.stringify(normalizeProvinceList(provinces)));
  };

  useEffect(() => {
    const initialProvinces = normalizeProvinceList(user?.preferred_provinces);
    if (initialProvinces.length > 0) {
      setSelectedProvinces(initialProvinces);
      return;
    }

    const storedProvinces = getStoredProvinceList();
    if (storedProvinces.length > 0) {
      setSelectedProvinces(storedProvinces);
    }
  }, [user?.preferred_provinces]);

  useEffect(() => {
    fetchTravelStyles();
    fetchProvinces();
    fetchUserProfile();
  }, []);

  const fetchTravelStyles = async () => {
    try {
      const response = await recommendationAPI.getTravelStyles();
      setTravelStyles(response.data.results || response.data);
    } catch (err) {
      console.error('Error fetching travel styles:', err);
    }
  };

  const fetchProvinces = async () => {
    try {
      const response = await recommendationAPI.getProvinces();
      const provincesList = Array.isArray(response.data) ? response.data : (response.data.results || []);
      setProvinces(provincesList);
    } catch (err) {
      console.error('Error fetching provinces:', err);
    }
  };

  const fetchUserProfile = async () => {
    try {
      const response = await recommendationAPI.getUserProfile();
      const profile = response.data;
      const profileProvinces = normalizeProvinceList(profile.preferred_provinces);
      const fallbackProvinces = normalizeProvinceList(user?.preferred_provinces);
      const storedProvinces = getStoredProvinceList();
      const resolvedProvinces = profileProvinces.length > 0
        ? profileProvinces
        : (fallbackProvinces.length > 0 ? fallbackProvinces : storedProvinces);
      
      setFormData((prev) => ({
        ...prev,
        budget: profile.budget ?? '',
        preferred_duration: profile.preferred_duration ?? '',
        preferred_season: profile.preferred_season || 'spring',
        preferred_travel_style_ids: profile.preferred_travel_style_ids || [],
      }));
      if (profile.latitude && profile.longitude) {
        setLocationData({
          latitude: parseFloat(profile.latitude),
          longitude: parseFloat(profile.longitude),
        });
      }
      // Load selected provinces - convert to strings for consistency
      setSelectedProvinces(resolvedProvinces);
      if (resolvedProvinces.length > 0) {
        storeProvinceSelection(resolvedProvinces);
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      const fallbackProvinces = normalizeProvinceList(user?.preferred_provinces);
      if (fallbackProvinces.length > 0) {
        setSelectedProvinces(fallbackProvinces);
      } else {
        const storedProvinces = getStoredProvinceList();
        if (storedProvinces.length > 0) {
          setSelectedProvinces(storedProvinces);
        }
      }
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    let newValue = value;

    if (name === 'budget' || name === 'preferred_duration') {
      if (value === '') {
        newValue = '';
      } else {
        const numericValue = parseFloat(value);
        newValue = Number.isNaN(numericValue) ? '' : Math.max(numericValue, 0);
      }
    }

    setFormData((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleLocationChange = (e) => {
    const { name, value } = e.target;
    setLocationData((prev) => ({
      ...prev,
      [name]: parseFloat(value),
    }));
  };

  const handleGetLiveLocation = () => {
    setLocationLoading(true);
    setLocationError('');

    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      setLocationLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setLocationData({
          latitude: parseFloat(latitude.toFixed(4)),
          longitude: parseFloat(longitude.toFixed(4)),
        });
        setLocationLoading(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        let errorMsg = 'Failed to get your location';
        if (error.code === error.PERMISSION_DENIED) {
          errorMsg = 'Please enable location access in your browser settings';
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          errorMsg = 'Location information is unavailable';
        } else if (error.code === error.TIMEOUT) {
          errorMsg = 'Location request timed out';
        }
        setLocationError(errorMsg);
        setLocationLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0,
      }
    );
  };

  const handleMapLocationSelected = (lat, lon) => {
    setLocationData({
      latitude: parseFloat(lat.toFixed(4)),
      longitude: parseFloat(lon.toFixed(4)),
    });
    setShowMapPicker(false);
  };

  const handleStyleToggle = (styleId) => {
    setFormData((prev) => ({
      ...prev,
      preferred_travel_style_ids: prev.preferred_travel_style_ids.includes(styleId)
        ? prev.preferred_travel_style_ids.filter((id) => id !== styleId)
        : [...prev.preferred_travel_style_ids, styleId],
    }));
  };

  const handleProvinceToggle = (provinceName) => {
    setSelectedProvinces((prev) =>
      prev.includes(provinceName)
        ? prev.filter((p) => p !== provinceName)
        : [...prev, provinceName]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const updateData = {
        preferred_season: formData.preferred_season,
        latitude: locationData.latitude,
        longitude: locationData.longitude,
        preferred_provinces: selectedProvinces,
        preferred_travel_style_ids: formData.preferred_travel_style_ids,
      };

      if (formData.budget !== '') {
        updateData.budget = parseFloat(formData.budget);
      }
      if (formData.preferred_duration !== '') {
        updateData.preferred_duration = parseInt(formData.preferred_duration);
      }

      await recommendationAPI.updateUserProfile(updateData);
      storeProvinceSelection(selectedProvinces);
      await refreshUserProfile();
      navigate('/home', { replace: true });
    } catch (err) {
      console.error('Update error:', err);
      const apiResponse = err.response?.data;
      const message = apiResponse?.error
        || (apiResponse && typeof apiResponse === 'object'
          ? Object.values(apiResponse).flat(Infinity).join(' ')
          : err.message || 'Failed to update preferences');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Travel Preferences</h1>
        <p className="text-gray-600 mb-8">
          Help us understand your travel style so we can recommend the best destinations for you.
        </p>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Budget */}
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
              Budget (NPR)
            </label>
            <input
              type="number"
              id="budget"
              name="budget"
              min="0"
              step="100"
              value={formData.budget}
              onChange={handleChange}
              placeholder="Enter your budget in NPR"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-2 text-sm text-gray-500">Current budget: ₹{formData.budget.toLocaleString()}</p>
          </div>

          {/* Duration */}
          <div>
            <label htmlFor="preferred_duration" className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Duration (days)
            </label>
            <input
              type="number"
              id="preferred_duration"
              name="preferred_duration"
              min="0"
              step="1"
              value={formData.preferred_duration}
              onChange={handleChange}
              placeholder="Enter duration in days"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-2 text-sm text-gray-500">Current duration: {formData.preferred_duration} days</p>
          </div>

          {/* Season */}
          <div>
            <label htmlFor="preferred_season" className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Season
            </label>
            <select
              id="preferred_season"
              name="preferred_season"
              value={formData.preferred_season}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="spring">Spring</option>
              <option value="summer">Summer</option>
              <option value="autumn">Autumn</option>
              <option value="winter">Winter</option>
            </select>
          </div>

          {/* Provinces */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Select Provinces (where to travel)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {provinces.length > 0 ? (
                provinces.map((province) => (
                  <label key={province} className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedProvinces.includes(String(province))}
                      onChange={() => handleProvinceToggle(String(province))}
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-gray-700">{province}</span>
                  </label>
                ))
              ) : (
                <p className="text-gray-500">Loading provinces...</p>
              )}
            </div>
            {selectedProvinces.length > 0 && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {selectedProvinces.join(', ')}
              </p>
            )}
          </div>

          {/* Travel Styles */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Travel Styles (select all that apply)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {travelStyles.map((style) => (
                <label key={style.id} className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.preferred_travel_style_ids.includes(style.id)}
                    onChange={() => handleStyleToggle(style.id)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-gray-700">{style.name}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Location */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Location</h3>
            
            {locationError && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
                {locationError}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label htmlFor="latitude" className="block text-sm font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  id="latitude"
                  name="latitude"
                  step="0.0001"
                  value={locationData.latitude}
                  onChange={handleLocationChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label htmlFor="longitude" className="block text-sm font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  id="longitude"
                  name="longitude"
                  step="0.0001"
                  value={locationData.longitude}
                  onChange={handleLocationChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              Current: Latitude {locationData.latitude}, Longitude {locationData.longitude}
            </p>

            <div className="flex gap-2 flex-wrap">
              <button
                type="button"
                onClick={handleGetLiveLocation}
                disabled={locationLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium text-sm"
              >
                {locationLoading ? 'Getting Location...' : 'Use Live Location'}
              </button>
              <button
                type="button"
                onClick={() => setShowMapPicker(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
              >
                Choose on Map
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? 'Saving...' : 'Save Preferences & Get Recommendations'}
          </button>
        </form>

        {showMapPicker && (
          <MapPicker
            initialLat={locationData.latitude}
            initialLon={locationData.longitude}
            onLocationSelected={handleMapLocationSelected}
            onClose={() => setShowMapPicker(false)}
          />
        )}
      </div>
    </div>
  );
}
