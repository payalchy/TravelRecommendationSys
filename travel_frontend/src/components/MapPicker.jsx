import React, { useEffect, useRef, useState } from 'react';

// Google Maps picker
export default function MapPicker({ initialLat, initialLon, onLocationSelected, onClose }) {
  const mapContainer = useRef(null);
  const [selectedLat, setSelectedLat] = useState(initialLat);
  const [selectedLon, setSelectedLon] = useState(initialLon);
  const [map, setMap] = useState(null);
  const markerRef = useRef(null);

  useEffect(() => {
    // Load Google Maps API
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyBXoZWW9Z3l8yOtBMt-uHstiTxmHaLWHpk&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initializeMap;
      document.head.appendChild(script);
    } else {
      initializeMap();
    }
  }, []);

  const initializeMap = () => {
    if (!mapContainer.current || !window.google) return;

    const mapOptions = {
      center: { lat: initialLat, lng: initialLon },
      zoom: 10,
      mapTypeControl: true,
      fullscreenControl: true,
      streetViewControl: false,
    };

    const newMap = new window.google.maps.Map(mapContainer.current, mapOptions);

    // Add marker at initial position
    const marker = new window.google.maps.Marker({
      position: { lat: initialLat, lng: initialLon },
      map: newMap,
      draggable: true,
      title: 'Your Location',
    });

    markerRef.current = marker;
    setMap(newMap);

    // Update coordinates when marker is dragged
    marker.addListener('drag', (event) => {
      setSelectedLat(event.latLng.lat());
      setSelectedLon(event.latLng.lng());
    });

    // Handle map clicks
    newMap.addListener('click', (e) => {
      const lat = e.latLng.lat();
      const lng = e.latLng.lng();
      
      setSelectedLat(lat);
      setSelectedLon(lng);
      marker.setPosition({ lat, lng });
    });
  };

  const handleConfirm = () => {
    onLocationSelected(selectedLat, selectedLon);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Choose Your Location</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Map Container */}
        <div className="flex-1 overflow-hidden">
          <div
            ref={mapContainer}
            style={{
              width: '100%',
              height: '100%',
              minHeight: '400px',
            }}
          />
        </div>

        {/* Info and Controls */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-gray-700 font-medium mb-2">Selected Location:</p>
            <p className="text-sm text-gray-600">
              Latitude: <span className="font-semibold">{selectedLat.toFixed(4)}</span>
              {' '} | Longitude: <span className="font-semibold">{selectedLon.toFixed(4)}</span>
            </p>
            <p className="text-xs text-gray-500 mt-2">
              💡 Click on the map, drag the marker, or search for a landmark to select a location
            </p>
          </div>

          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Confirm Location
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
