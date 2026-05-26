import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function HomePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');

  useEffect(() => {
    if (user) {
      fetchRecommendations();
    }
  }, [user]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);

      const payload = {
        user_latitude: user?.latitude || 27.7172,
        user_longitude: user?.longitude || 85.324,
      };

      if (user?.budget) payload.budget = user.budget;
      if (user?.preferred_duration) payload.duration = user.preferred_duration;
      if (user?.preferred_season) payload.preferred_season = user.preferred_season;
      if (user?.preferred_provinces && user.preferred_provinces.length > 0) {
        payload.preferred_provinces = user.preferred_provinces;
      }

      const response = await recommendationAPI.getRecommendations(payload);
      setDestinations(response.data.destination_results || []);
    } catch (err) {
      setError(
        err.response?.data?.error || 'Failed to fetch recommendations'
      );
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Destination Search
  const handleDestinationSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setSearchError('Enter a destination name');
      return;
    }

    try {
      setSearchLoading(true);
      setSearchError('');

      const response = await recommendationAPI.searchDestinations(
        searchQuery.trim()
      );

      setSearchResults(response.data.results || []);
    } catch (err) {
      setSearchError(
        err.response?.data?.error || 'Failed to search destinations'
      );

      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  };

  const hasPreferences =
    user?.budget > 0 &&
    user?.preferred_duration > 0 &&
    Boolean(user?.preferred_season);

  const handleDestinationClick = (destination) => {
    navigate(`/destination/${destination.destination_id}`, {
      state: { destination },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Personalized Travel Recommendations System
            </h1>

            <p className="text-gray-600 mt-1">
              Personalized destinations for you
            </p>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/profile')}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 transition"
            >
              Profile
            </button>

            <button
              onClick={() => navigate('/preferences')}
              className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition"
            >
              Update Preferences
            </button>

            <button
              onClick={logout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Search Bar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Search Destinations
          </h2>

          <form
            onSubmit={handleDestinationSearch}
            className="flex flex-col gap-4 md:flex-row"
          >
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by destination name, province, or tag"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            <button
              type="submit"
              disabled={searchLoading}
              className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {searchLoading ? 'Searching...' : 'Search'}
            </button>
          </form>

          {searchError && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
              {searchError}
            </div>
          )}

          {searchResults.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Search Results
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {searchResults.map((destination) => (
                  <div
                    key={destination.destination_id}
                    className="bg-gray-50 rounded-xl border border-gray-200 p-5"
                  >
                    <h4 className="text-lg font-bold text-gray-900">
                      {destination.name}
                    </h4>

                    <p className="text-sm text-gray-500 mt-1">
                      {destination.province}
                    </p>

                    <button
                      type="button"
                      onClick={() => handleDestinationClick(destination)}
                      className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                    >
                      View Details
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg mb-8">
            {error}

            <button
              onClick={fetchRecommendations}
              className="ml-4 underline font-semibold hover:no-underline"
            >
              Try Again
            </button>
          </div>
        )}

        {!hasPreferences && (
          <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 px-6 py-4 rounded-lg mb-8">
            <p className="font-semibold">Preferences incomplete</p>

            <p className="mt-1 text-sm">
              Update your budget, preferred duration, and season so
              recommendations match your needs.
            </p>

            <button
              onClick={() => navigate('/preferences')}
              className="mt-4 inline-flex items-center rounded-lg bg-yellow-200 px-4 py-2 text-sm font-medium text-yellow-900 hover:bg-yellow-300"
            >
              Complete Preferences
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-24">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
          </div>
        ) : destinations.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">
              No recommendations found. Try updating your preferences.
            </p>

            <button
              onClick={() => navigate('/preferences')}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Update Preferences
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <p className="text-gray-600">
                Found {destinations.length} destinations based on your
                preferences
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {destinations.map((destination, index) => (
                <div
                  key={destination.destination_id}
                  className="bg-white rounded-xl border border-gray-200 shadow-sm transition hover:shadow-xl"
                >
                  <div className="flex items-center justify-between gap-4 p-5">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-lg">
                        {index + 1}
                      </div>

                      <div>
                        <button
                          type="button"
                          onClick={() =>
                            handleDestinationClick(destination)
                          }
                          className="text-xl font-bold text-gray-900 hover:text-blue-600 text-left"
                        >
                          {destination.name}
                        </button>

                        <p className="text-sm text-gray-500 mt-1">
                          {destination.province}
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        if (
                          destination.latitude &&
                          destination.longitude
                        ) {
                          window.open(
                            `https://www.google.com/maps/search/?api=1&query=${destination.latitude},${destination.longitude}`,
                            '_blank'
                          );
                        }
                      }}
                      className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition"
                    >
                      View in Map
                    </button>
                  </div>

                  <div className="border-t border-gray-100 px-5 py-4">
                    {destination.latitude != null &&
                      destination.longitude != null && (
                        <p className="text-sm text-gray-500 mb-4">
                          ({destination.latitude.toFixed(4)},{' '}
                          {destination.longitude.toFixed(4)})
                        </p>
                      )}

                    <div className="flex flex-wrap gap-3">
                      <button
                        type="button"
                        className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:border-blue-600 hover:text-blue-600 transition"
                      >
                        Wishlist
                      </button>

                      <button
                        type="button"
                        className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:border-blue-600 hover:text-blue-600 transition"
                      >
                        Visited
                      </button>

                      <button
                        type="button"
                        className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:border-blue-600 hover:text-blue-600 transition"
                      >
                        Interested
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}