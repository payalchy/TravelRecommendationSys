import React, { useState } from 'react';
import { recommendationAPI } from '../services/api';
import DestinationCard from '../components/DestinationCard';
import SearchForm from '../components/SearchForm';

export default function RecommendationPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (filters) => {
    setLoading(true);
    setError(null);

    try {
      const response = await recommendationAPI.getRecommendations(filters);
      setRecommendations(response.data.destination_results || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch recommendations');
      console.error('Recommendation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDestinationSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchError('Enter a place name or city to search.');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);

    try {
      const response = await recommendationAPI.searchDestinations(searchQuery.trim());
      setSearchResults(response.data.results || []);
    } catch (err) {
      setSearchError(err.response?.data?.error || 'Failed to search destinations');
      console.error('Destination search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8 text-center text-gray-900">
        Travel Recommendations
      </h1>

      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Search destination</h2>
        <form onSubmit={handleDestinationSearch} className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search destination by name, city or tag"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={searchLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {searchLoading ? 'Searching...' : 'Search'}
          </button>
        </form>
        {searchError && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {searchError}
          </div>
        )}
        {searchResults.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Search results</h3>
            <div className="grid grid-cols-1 gap-4">
              {searchResults.map((destination, idx) => (
                <DestinationCard key={destination.destination_id} destination={destination} index={idx} />
              ))}
            </div>
          </div>
        )}
      </div>

      <SearchForm onSearch={handleSearch} loading={loading} />

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="grid grid-cols-1 gap-6 mt-8">
          {recommendations.map((dest, idx) => (
            <DestinationCard key={idx} destination={dest} index={idx} />
          ))}
        </div>
      )}

      {!loading && recommendations.length === 0 && !error && (
        <div className="text-center py-12 text-gray-500">
          <p>Enter your preferences to get personalized recommendations</p>
        </div>
      )}
    </div>
  );
}
