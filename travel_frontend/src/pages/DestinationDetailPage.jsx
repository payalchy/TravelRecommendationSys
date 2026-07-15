import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { recommendationAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function DestinationDetailPage() {
  const { destinationId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedPackages, setExpandedPackages] = useState({});

  const destination = location.state?.destination;

  useEffect(() => {
    if (!destination) {
      navigate('/home');
      return;
    }

    fetchDestinationPackages();
  }, [destinationId]);

  const fetchDestinationPackages = async () => {
    try {
      setLoading(true);

      const response =
        await recommendationAPI.getDestinationPackages(
          destinationId
        );

      setPackages(response.data.packages || []);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          'Failed to fetch packages'
      );

      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleItinerary = (packageId) => {
    setExpandedPackages((prev) => ({
      ...prev,
      [packageId]: !prev[packageId],
    }));
  };

  const handleViewMap = () => {
    const userLat = user?.latitude;
    const userLon = user?.longitude;
    const destLat = destination?.latitude;
    const destLon = destination?.longitude;

    if (userLat == null || userLon == null || destLat == null || destLon == null) {
      return;
    }

    const url = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(`${userLat},${userLon}`)}&destination=${encodeURIComponent(`${destLat},${destLon}`)}&travelmode=driving`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  if (!destination) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/home')}
            className="text-blue-600 hover:text-blue-800 font-semibold mb-2"
          >
            ← Back to Recommendations
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Destination Header */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
          {/* Destination Image */}
          {destination.image && (
            <div className="h-72 overflow-hidden">
              <img
                src={destination.image}
                alt={destination.name}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-8">
            <div className="flex flex-col gap-3">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">
                  {destination.name}
                </h2>

                <p className="text-sm text-gray-500 mt-1">
                  {destination.province}
                </p>
              </div>

              {/* View on Map Button */}

              {/* Destination Ratings */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <p className="text-sm text-gray-600">
                    Culture
                  </p>
                  <p className="font-bold text-blue-700">
                    {destination.culture}
                  </p>
                </div>

                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <p className="text-sm text-gray-600">
                    Adventure
                  </p>
                  <p className="font-bold text-red-700">
                    {destination.adventure}
                  </p>
                </div>

                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <p className="text-sm text-gray-600">
                    Wildlife
                  </p>
                  <p className="font-bold text-green-700">
                    {destination.wildlife}
                  </p>
                </div>

                <div className="bg-yellow-50 p-3 rounded-lg text-center">
                  <p className="text-sm text-gray-600">
                    Sightseeing
                  </p>
                  <p className="font-bold text-yellow-700">
                    {destination.sightseeing}
                  </p>
                </div>

                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <p className="text-sm text-gray-600">
                    History
                  </p>
                  <p className="font-bold text-purple-700">
                    {destination.history}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Packages Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">
            Available Travel Packages
          </h2>

          {/* Error */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
            </div>
          ) : packages.length === 0 ? (
            <div className="bg-gray-100 rounded-lg p-12 text-center">
              <p className="text-gray-600 text-lg">
                No packages available for this destination
                at the moment.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {packages.map((pkg) => (
                <div
                  key={pkg.package_id}
                  className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-2xl transition"
                >
                  {/* Package Image */}
                  {pkg.image ? (
                    <div className="h-56 overflow-hidden bg-gray-200">
                      <img
                        src={pkg.image}
                        alt={pkg.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="h-56 flex items-center justify-center bg-gray-200">
                      <p className="text-gray-500">
                        No Image Available
                      </p>
                    </div>
                  )}

                  <div className="p-6">
                    {/* Package Name */}
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">
                      {pkg.name}
                    </h3>

                    {/* Description */}
                    <p className="text-gray-600 mb-5 line-clamp-3">
                      {pkg.description}
                    </p>

                    {/* Package Details */}
                    <div className="grid grid-cols-2 gap-4 mb-6 bg-gray-50 p-4 rounded-lg">
                      <div>
                        <p className="text-xs text-gray-500 font-semibold uppercase">
                          Duration
                        </p>

                        <p className="text-lg font-bold text-gray-900">
                          {pkg.days || pkg.duration_days || 'N/A'} days
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 font-semibold uppercase">
                          Budget
                        </p>

                        <p className="text-lg font-bold text-green-600">
                          NPR{' '}
                          {pkg.budget ||
                            pkg.price_npr ||
                            'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 font-semibold uppercase">
                          Transport
                        </p>

                        <p className="text-sm font-semibold text-gray-700">
                          {pkg.transport_mode ||
                            pkg.transport_type ||
                            'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 font-semibold uppercase">
                          Type
                        </p>

                        <p className="text-sm font-semibold text-gray-700">
                          {pkg.package_type ||
                            pkg.guide_type ||
                            'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 font-semibold uppercase">
                          Travelers
                        </p>

                        <p className="text-sm font-semibold text-gray-700">
                          {pkg.number_of_travelers || 'N/A'}
                        </p>
                      </div>
                    </div>

                    {/* Locations */}
                    <div className="border-t pt-4 mb-6">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-black">
                          <strong>From:</strong>{' '}
                          {pkg.start_location || 'N/A'}
                        </span>

                        <span className="text-black">
                          <strong>To:</strong>{' '}
                          {pkg.end_location || 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Includes */}
                    {Array.isArray(pkg.includes) && pkg.includes.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-semibold text-green-700 mb-2">
                          Includes
                        </h4>

                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                          {pkg.includes.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Excludes */}
                    {Array.isArray(pkg.excludes) && pkg.excludes.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-semibold text-red-700 mb-2">
                          Excludes
                        </h4>

                        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                          {pkg.excludes.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="flex gap-3 flex-wrap">
                      <button
                        onClick={() =>
                          toggleItinerary(pkg.package_id)
                        }
                        className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold"
                      >
                        {expandedPackages[pkg.package_id]
                          ? 'Hide Itinerary'
                          : 'View Full Itinerary'}
                      </button>
                      <button
                        onClick={() => navigate(`/booking/${pkg.package_id}`)}
                        className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold"
                      >
                        Booking
                      </button>
                    </div>

                    {/* Itinerary */}
                    {expandedPackages[pkg.package_id] && (
                      <div className="mt-6 border-t pt-6">
                        <h4 className="text-xl font-bold text-gray-900 mb-4">
                          Travel Itinerary
                        </h4>

                        {pkg.itinerary &&
                        pkg.itinerary.length > 0 ? (
                          <div className="space-y-6">
                            {pkg.itinerary.map(
                              (day, index) => (
                                <div
                                  key={index}
                                  className="border rounded-lg overflow-hidden bg-gray-50"
                                >
                                  {/* Itinerary Image */}
                                  {day.image && (
                                    <div className="h-48 overflow-hidden">
                                      <img
                                        src={day.image}
                                        alt={
                                          day.destination
                                        }
                                        className="w-full h-full object-cover"
                                      />
                                    </div>
                                  )}

                                  <div className="p-4">
                                    <div className="flex items-center gap-3 mb-2">
                                      <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                                        Day{' '}
                                        {day.day_number}
                                      </div>

                                      <h5 className="font-bold text-lg text-black">
                                        {day.destination}
                                      </h5>
                                    </div>

                                    <p className="text-gray-700">
                                      {day.description}
                                    </p>
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        ) : (
                          <div className="bg-gray-100 rounded-lg p-6 text-center">
                            <p className="text-gray-600">
                              No itinerary details available.
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

    </div>
  );
}