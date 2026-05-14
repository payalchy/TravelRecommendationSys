import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function DestinationCard({ destination, index }) {
  const navigate = useNavigate();

  const handleDestinationClick = () => {
    navigate(`/destination/${destination.destination_id}`, {
      state: { destination },
    });
  };

  const handleViewMap = () => {
    if (destination.latitude && destination.longitude) {
      window.open(
        `https://www.google.com/maps/search/?api=1&query=${destination.latitude},${destination.longitude}`,
        '_blank'
      );
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden transition hover:shadow-xl">
      
      {/* Destination Header */}
      <div className="p-6 flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        
        {/* Left Section */}
        <div className="flex items-center gap-4">
          
          {/* Index Circle */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-lg">
            {index + 1}
          </div>

          {/* Destination Info */}
          <div>
            <button
              type="button"
              onClick={handleDestinationClick}
              className="text-2xl font-bold text-gray-900 hover:text-blue-600 transition text-left"
            >
              {destination.name}
            </button>

            <p className="text-sm text-gray-500 mt-1">
              {destination.province}
            </p>

            {destination.latitude != null &&
              destination.longitude != null && (
                <p className="text-sm text-gray-400 mt-1">
                  ({destination.latitude.toFixed(4)},{' '}
                  {destination.longitude.toFixed(4)})
                </p>
              )}
          </div>
        </div>

        {/* Right Buttons */}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleViewMap}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            View in Map
          </button>

          <button
            type="button"
            onClick={handleDestinationClick}
            className="rounded-xl border border-blue-600 px-5 py-3 text-sm font-semibold text-blue-600 hover:bg-blue-50 transition"
          >
            View Packages
          </button>
        </div>
      </div>

      {/* Destination Scores */}
      <div className="border-t border-gray-100 px-6 py-5 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">

          <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold">
              Culture
            </p>
            <p className="text-lg font-bold text-gray-900">
              {destination.culture ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold">
              Adventure
            </p>
            <p className="text-lg font-bold text-gray-900">
              {destination.adventure ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold">
              Wildlife
            </p>
            <p className="text-lg font-bold text-gray-900">
              {destination.wildlife ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold">
              Sightseeing
            </p>
            <p className="text-lg font-bold text-gray-900">
              {destination.sightseeing ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold">
              History
            </p>
            <p className="text-lg font-bold text-gray-900">
              {destination.history ?? 0}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mt-5">
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
  );
}