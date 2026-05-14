import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { recommendationAPI } from '../services/api';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchHistory, setSearchHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSearchHistory();
  }, []);

  const fetchSearchHistory = async () => {
    try {
      setLoading(true);
      const response = await recommendationAPI.getUserSearchHistory();
      setSearchHistory(response.data || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load search history');
      console.error('Search history error:', err);
    } finally {
      setLoading(false);
    }
  };

  const profileUsername =
    user?.username || user?.user?.username || 'Unknown user';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-4 md:flex-row items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
            <p className="text-gray-600 mt-1">Username and search history only.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/home')}
              className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition"
            >
              Back to Recommendations
            </button>
            <button
              type="button"
              onClick={logout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900">Username</h2>
          <p className="mt-2 text-lg font-semibold text-gray-900">{profileUsername}</p>
        </section>

        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">Search History</h2>
              <p className="text-gray-600 mt-1">Saved recommendation searches for this account.</p>
            </div>
            <button
              type="button"
              onClick={fetchSearchHistory}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              Refresh
            </button>
          </div>

          {error && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : searchHistory.length === 0 ? (
            <div className="mt-8 text-center text-gray-500">
              <p>No search history yet. Run a recommendation search to save the results.</p>
            </div>
          ) : (
            <div className="mt-8 space-y-6">
              {searchHistory.map((entry) => (
                <div key={entry.id} className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Searched on</p>
                      <p className="mt-1 text-base font-semibold text-gray-900">{new Date(entry.created_at).toLocaleString()}</p>
                    </div>
                    <div className="space-y-1 text-right">
                      <p className="text-sm text-gray-500">Budget</p>
                      <p className="text-sm font-medium text-gray-900">{entry.search_payload?.budget ? `₹${Number(entry.search_payload.budget).toLocaleString()}` : 'Any'}</p>
                      <p className="text-sm text-gray-500">Duration</p>
                      <p className="text-sm font-medium text-gray-900">{entry.search_payload?.duration || 'Any'} days</p>
                      <p className="text-sm text-gray-500">Season</p>
                      <p className="text-sm font-medium text-gray-900">{entry.search_payload?.preferred_season || 'Any'}</p>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {(entry.destination_results || []).slice(0, 6).map((destination) => (
                      <div key={destination.destination_id} className="rounded-2xl border border-gray-200 bg-white p-4">
                        <p className="text-sm font-semibold text-gray-900">{destination.name}</p>
                        <p className="mt-1 text-sm text-gray-500">{destination.province}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
