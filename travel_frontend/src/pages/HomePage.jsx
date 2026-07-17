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
  const [suggestedDestinations, setSuggestedDestinations] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [suggestionsError, setSuggestionsError] = useState('');
  const [recommendedPackages, setRecommendedPackages] = useState([]);
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [packagesError, setPackagesError] = useState('');

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [searchCount, setSearchCount] = useState(0);
  const [searchOffset, setSearchOffset] = useState(0);
  const [hasMoreSearchResults, setHasMoreSearchResults] = useState(false);
  const [distanceLabels, setDistanceLabels] = useState({});
  const [showFollowUpRecommendations, setShowFollowUpRecommendations] = useState(false);

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

  const getStoredProvinceList = () => normalizeProvinceList(localStorage.getItem('preferred_provinces'));

  const buildRecommendationPayload = ({ saveHistory = true } = {}) => {
    const payload = {
      user_latitude: user?.latitude || 27.7172,
      user_longitude: user?.longitude || 85.324,
      save_history: saveHistory,
    };

    if (user?.budget) payload.budget = user.budget;

    if (user?.preferred_duration) {
      payload.duration = user.preferred_duration;
    }

    if (user?.preferred_season) {
      payload.preferred_season = user.preferred_season;
    }

    const preferredProvinces = normalizeProvinceList(user?.preferred_provinces);
    const fallbackProvinces = getStoredProvinceList();

    if (preferredProvinces.length > 0 || fallbackProvinces.length > 0) {
      payload.preferred_provinces = preferredProvinces.length > 0 ? preferredProvinces : fallbackProvinces;
    }

    return payload;
  };

  useEffect(() => {
    if (user) {
      fetchRecommendations({ saveHistory: false });
      fetchRecommendedPackages();
      fetchSearchHistory();
    }
  }, [user]);

  const getDrivingDistanceLabel = async (destination, userLat, userLon) => {
    if (!destination?.latitude || !destination?.longitude || !userLat || !userLon) {
      return null;
    }

    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/directions/json?origin=${userLat},${userLon}&destination=${destination.latitude},${destination.longitude}&mode=driving&units=metric&key=AIzaSyBXoZWW9Z3l8yOtBMt-uHstiTxmHaLWHpk`
      );
      const data = await response.json();

      if (data.status === 'OK' && data.routes?.[0]?.legs?.[0]?.distance?.value) {
        const km = (data.routes[0].legs[0].distance.value / 1000).toFixed(1);
        return `${km} km`;
      }
    } catch (error) {
      console.error('Distance lookup failed:', error);
    }

    return null;
  };

  const loadDrivingDistances = async (items) => {
    setDistanceLabels({});

    const userLat = user?.latitude || 27.7172;
    const userLon = user?.longitude || 85.324;

    const results = await Promise.all(
      items.map(async (destination) => {
        const distanceText = await getDrivingDistanceLabel(destination, userLat, userLon);
        const destinationId = destination.destination_id || destination.id;
        return [destinationId, distanceText];
      })
    );

    const nextDistances = {};
    results.forEach(([destinationId, distanceText]) => {
      if (destinationId && distanceText) {
        nextDistances[destinationId] = distanceText;
      }
    });

    setDistanceLabels(nextDistances);
  };

  const fetchRecommendations = async ({ saveHistory = true } = {}) => {
    try {
      setLoading(true);

      const response = await recommendationAPI.getRecommendations(buildRecommendationPayload({ saveHistory }));

      const recommendations = response.data.destination_results || [];
      setDestinations(recommendations);

      if (recommendations.length > 0) {
        await loadDrivingDistances(recommendations);
      }

    } catch (err) {

      setError(
        err.response?.data?.error ||
          'Failed to fetch recommendations'
      );

      console.error('Error:', err);

    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendedPackages = async () => {
    try {
      setPackagesLoading(true);
      setPackagesError('');

      const response = await recommendationAPI.getRecommendedPackages(buildRecommendationPayload({ saveHistory: false }));
      setRecommendedPackages(response.data.packages || []);
    } catch (err) {
      setPackagesError(err.response?.data?.error || 'Failed to fetch recommended packages');
      console.error('Package recommendation error:', err);
    } finally {
      setPackagesLoading(false);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const response = await recommendationAPI.getUserSearchHistory();
      const history = Array.isArray(response.data) ? response.data : [];
      const shouldShowFollowUp = history.length >= 2;

      setShowFollowUpRecommendations(shouldShowFollowUp);

      if (shouldShowFollowUp) {
        fetchYouMightAlsoLike();
      }
    } catch (err) {
      console.error('Search history error:', err);
      setShowFollowUpRecommendations(false);
    }
  };

  const fetchYouMightAlsoLike = async () => {
    try {
      setSuggestionsLoading(true);
      setSuggestionsError('');

      const response = await recommendationAPI.getYouMightAlsoLike(6);
      setSuggestedDestinations(response.data.results || []);
    } catch (err) {
      setSuggestionsError(
        err.response?.data?.error ||
          'Failed to load suggestions'
      );

      console.error('Suggestion error:', err);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  // AUTO SEARCH
  const handleDestinationSearch = async (query, append = false) => {

    const trimmedQuery = query.trim();
    setSearchQuery(query);

    if (!trimmedQuery) {
      setSearchResults([]);
      setSearchCount(0);
      setSearchOffset(0);
      setHasMoreSearchResults(false);
      return;
    }

    try {

      setSearchLoading(true);
      setSearchError('');

      const currentOffset = append ? searchOffset : 0;
      const response = await recommendationAPI.searchDestinations(
        trimmedQuery,
        currentOffset,
        6
      );

      const nextResults = response.data.results || [];
      const totalCount = response.data.count || 0;

      setSearchResults((prev) => append ? [...prev, ...nextResults] : nextResults);
      setSearchCount(totalCount);
      setSearchOffset(currentOffset + nextResults.length);
      setHasMoreSearchResults(Boolean(response.data.has_more));

    } catch (err) {

      setSearchError(
        err.response?.data?.error ||
          'Failed to search destinations'
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
    navigate(
      `/destination/${destination.destination_id}`,
      {
        state: { destination },
      }
    );
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

        {/* SEARCH */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">

          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Search Destinations
          </h2>

          <div className="flex flex-col gap-4 md:flex-row">

            <input
              type="text"
              value={searchQuery}
              onChange={(e) =>
                handleDestinationSearch(e.target.value)
              }
              placeholder="Search by destination name, province, or tag"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

          </div>

          {searchLoading && (
            <p className="mt-4 text-blue-600">
              Searching...
            </p>
          )}

          {searchError && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
              {searchError}
            </div>
          )}

          {searchResults.length > 0 && (
            <div className="mt-6">

              <div className="flex flex-wrap items-center gap-2 mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Search Results
                </h3>
                <span className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                  {searchCount} relevant destinations
                </span>
              </div>

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
                      onClick={() =>
                        handleDestinationClick(destination)
                      }
                      className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                    >
                      View Details
                    </button>

                  </div>
                ))}

              </div>

              {hasMoreSearchResults && (
                <div className="mt-5 text-center">
                  <button
                    type="button"
                    onClick={() => handleDestinationSearch(searchQuery, true)}
                    className="px-5 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
                  >
                    Load More
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg mb-8">

            {error}

            <button
              onClick={() => fetchRecommendations({ saveHistory: false })}
              className="ml-4 underline font-semibold hover:no-underline"
            >
              Try Again
            </button>

          </div>
        )}

        {!hasPreferences && (
          <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 px-6 py-4 rounded-lg mb-8">

            <p className="font-semibold">
              Preferences incomplete
            </p>

            <p className="mt-1 text-sm">
              Update your budget, preferred duration,
              and season so recommendations match
              your needs.
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
              No recommendations found.
            </p>

          </div>

        ) : (

          <>
            <div className="mb-6">
              <p className="text-gray-600">
                Found {destinations.length} destinations
                based on your preferences
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
                          onClick={() => handleDestinationClick(destination)}
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
                        if (destination.latitude && destination.longitude) {
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

                    <button
                      type="button"
                      onClick={() => handleDestinationClick(destination)}
                      className="rounded-xl border border-blue-600 px-4 py-3 text-sm font-semibold text-blue-600 hover:bg-blue-50 transition"
                    >
                      Details
                    </button>
                  </div>

                  <div className="border-t border-gray-100 px-5 py-4">
                    <p className="text-sm text-gray-500 mb-4">
                      {(() => {
                        const destinationId = destination.destination_id || destination.id;
                        const label = distanceLabels[destinationId];
                        if (label) {
                          return `Driving distance: ${label}`;
                        }
                        if (destination.distance_km != null) {
                          return `Approx. straight-line distance: ${destination.distance_km.toFixed(2)} km`;
                        }
                        return 'Distance unavailable';
                      })()}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {showFollowUpRecommendations && (
              <div className="mt-14 border-t border-gray-200 pt-10">
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">
                    You Might Also Like
                  </h2>
                </div>

                {suggestionsLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {[...Array(6)].map((_, index) => (
                      <div
                        key={index}
                        className="h-44 rounded-xl border border-gray-200 bg-white animate-pulse"
                      />
                    ))}
                  </div>
                ) : suggestionsError ? (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 px-6 py-4 text-amber-800">
                    {suggestionsError}
                  </div>
                ) : suggestedDestinations.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {suggestedDestinations.map((destination, index) => (
                      <div
                        key={destination.destination_id}
                        className="bg-white rounded-xl border border-gray-200 shadow-sm transition hover:shadow-xl"
                      >
                        <div className="flex items-center justify-between gap-4 p-5">
                          <div className="flex items-center gap-4 min-w-0">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-blue-500 text-white font-bold text-lg shrink-0">
                              {index + 1}
                            </div>

                            <div className="min-w-0">
                              <button
                                type="button"
                                onClick={() => handleDestinationClick(destination)}
                                className="text-xl font-bold text-gray-900 hover:text-blue-600 text-left truncate block max-w-full"
                              >
                                {destination.name}
                              </button>

                              <p className="text-sm text-gray-500 mt-1 truncate">
                                {destination.province}
                              </p>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => {
                              if (destination.latitude && destination.longitude) {
                                window.open(
                                  `https://www.google.com/maps/search/?api=1&query=${destination.latitude},${destination.longitude}`,
                                  '_blank'
                                );
                              }
                            }}
                            className="rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                          >
                            View in Map
                          </button>
                        </div>

                        <div className="border-t border-gray-100 px-5 py-4">
                          <div className="flex items-center justify-end">
                            <button
                              type="button"
                              onClick={() => handleDestinationClick(destination)}
                              className="font-semibold text-blue-600 hover:text-blue-700"
                            >
                              View Details
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-gray-200 bg-white px-6 py-4 text-gray-600">
                    No personalized suggestions yet. Search a few destinations or update your profile to build this section.
                  </div>
                )}
              </div>
            )}

            <div className="mt-14 border-t border-gray-200 pt-10">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                  Recommended Packages
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Best-match packages ranked from your saved preferences.
                </p>
              </div>

              {packagesLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {[...Array(6)].map((_, index) => (
                    <div
                      key={index}
                      className="h-96 rounded-3xl border border-gray-200 bg-white animate-pulse"
                    />
                  ))}
                </div>
              ) : packagesError ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-6 py-4 text-amber-800">
                  {packagesError}
                </div>
              ) : recommendedPackages.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {recommendedPackages.map((pkg) => (
                    <div
                      key={pkg.package_id}
                      className="overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl"
                    >
                      <div className="relative h-52 bg-gray-100">
                        {pkg.image ? (
                          <img
                            src={pkg.image}
                            alt={pkg.name}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center bg-gradient-to-br from-slate-100 to-blue-50">
                            <span className="text-sm font-medium text-gray-400">
                              No package image
                            </span>
                          </div>
                        )}

                        <div className="absolute left-4 top-4 rounded-full bg-white/95 px-3 py-1 text-xs font-semibold text-blue-700 shadow-sm backdrop-blur">
                          {pkg.recommendation_reason || 'Best match'}
                        </div>
                      </div>

                      <div className="p-6">
                        <div className="mb-3 flex items-start justify-between gap-3">
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">
                              {pkg.name}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">
                              {pkg.destination_name || pkg.province || 'Nepal'}
                            </p>
                          </div>

                          <div className="rounded-2xl bg-blue-50 px-3 py-2 text-right">
                            <p className="text-[11px] font-semibold uppercase tracking-wide text-blue-700">
                              Match
                            </p>
                            <p className="text-lg font-bold text-blue-700">
                              {Math.round((pkg.match_score || 0) * 100)}%
                            </p>
                          </div>
                        </div>

                        <p className="mb-4 line-clamp-3 text-sm leading-6 text-gray-600">
                          {pkg.description}
                        </p>

                        <div className="grid grid-cols-2 gap-3 rounded-2xl bg-gray-50 p-4 text-sm">
                          <div>
                            <p className="text-gray-500">Budget</p>
                            <p className="font-semibold text-gray-900">
                              NPR {Number(pkg.budget || 0).toLocaleString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Duration</p>
                            <p className="font-semibold text-gray-900">
                              {pkg.days || 'N/A'} days
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Transport</p>
                            <p className="font-semibold text-gray-900 capitalize">
                              {pkg.transport_mode || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Type</p>
                            <p className="font-semibold text-gray-900 capitalize">
                              {pkg.package_type || 'N/A'}
                            </p>
                          </div>
                        </div>

                        <div className="mt-5 flex items-center justify-end gap-3">
                          <button
                            type="button"
                            onClick={() => pkg.package_id && navigate(`/package/${pkg.package_id}`)}
                            className="rounded-xl border border-blue-600 px-4 py-2 text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
                          >
                            Details
                          </button>
                          <button
                            type="button"
                            onClick={() => pkg.package_id && navigate(`/booking/${pkg.package_id}`)}
                            className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700"
                          >
                            Booking
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-gray-200 bg-white px-6 py-4 text-gray-600">
                  No package matches found yet. Update your preferences to improve the ranking.
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}