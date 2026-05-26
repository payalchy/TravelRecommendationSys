import React, { useState, useEffect } from 'react';
import { recommendationAPI } from '../services/api';

export default function SearchForm({ onSearch, loading }) {
  const [location, setLocation] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [budget, setBudget] = useState('');
  const [duration, setDuration] = useState('');
  const [season, setSeason] = useState('');
  const [provinces, setProvinces] = useState([]);
  const [selectedProvinces, setSelectedProvinces] = useState([]);
  const [geocodingLoading, setGeocodingLoading] = useState(false);
  const [provincesLoading, setProvincesLoading] = useState(false);

  useEffect(() => {
    // Fetch available provinces on component mount
    fetchProvinces();
  }, []);

  const fetchProvinces = async () => {
    try {
      setProvincesLoading(true);
      const response = await recommendationAPI.getProvinces();
      const provincesList = Array.isArray(response.data) ? response.data : (response.data.results || []);
      setProvinces(provincesList);
    } catch (err) {
      console.error('Error fetching provinces:', err);
    } finally {
      setProvincesLoading(false);
    }
  };

  const handleGeocodeLocation = async (e) => {
    e.preventDefault();
    if (!location.trim()) return;

    setGeocodingLoading(true);
    try {
      const response = await recommendationAPI.geocodeDestination(location);
      setLatitude(response.data.latitude);
      setLongitude(response.data.longitude);
    } catch (err) {
      console.error('Geocoding error:', err);
      alert('Could not find location. Please enter coordinates manually.');
    } finally {
      setGeocodingLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!latitude || !longitude) {
      alert('Please enter or geocode a location');
      return;
    }

    const payload = {
      user_latitude: parseFloat(latitude),
      user_longitude: parseFloat(longitude),
    };

    if (budget) payload.budget = parseFloat(budget);
    if (duration) payload.duration = parseFloat(duration);
    if (season) payload.preferred_season = season;
    if (selectedProvinces.length > 0) {
      // Send selected provinces as filter
      payload.preferred_provinces = selectedProvinces;
    }

    onSearch(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 mb-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        
        {/* Location Input */}
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Starting Location
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Enter city name (e.g., Kathmandu)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
            <button
              onClick={handleGeocodeLocation}
              disabled={geocodingLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {geocodingLoading ? 'Locating...' : 'Locate'}
            </button>
          </div>
        </div>

        {/* Budget */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Budget (NPR)
          </label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            placeholder="e.g., 50000"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          />
        </div>

        {/* Duration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duration (Days)
          </label>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder="e.g., 5"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          />
        </div>

        {/* Season */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Season
          </label>
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          >
            <option value="">Select season</option>
            <option value="spring">Spring</option>
            <option value="summer">Summer</option>
            <option value="autumn">Autumn</option>
            <option value="winter">Winter</option>
          </select>
        </div>

        {/* Provinces */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Provinces
          </label>
          <select
            multiple
            value={selectedProvinces}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              setSelectedProvinces(selected);
            }}
            disabled={provincesLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          >
            {provinces.map((province) => (
              <option key={province} value={province}>
                {province}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
        </div>

        {/* Latitude */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Latitude
          </label>
          <input
            type="number"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            placeholder="27.7172"
            step="0.0001"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          />
        </div>

        {/* Longitude */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Longitude
          </label>
          <input
            type="number"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            placeholder="85.3240"
            step="0.0001"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-4 w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-semibold"
      >
        {loading ? 'Searching...' : 'Get Recommendations'}
      </button>
    </form>
  );
}
