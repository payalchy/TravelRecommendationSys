import React, { useEffect, useRef, useState } from 'react';

export default function RouteMap({ userLat, userLon, destLat, destLon, destName, onClose }) {
  const mapContainer = useRef(null);
  const [map, setMap] = useState(null);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const userMarkerRef = useRef(null);
  const destMarkerRef = useRef(null);
  const polylineRef = useRef(null);

  useEffect(() => {
    // Load Google Maps API
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyBXoZWW9Z3l8yOtBMt-uHstiTxmHaLWHpk&libraries=routes`;
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

    // Calculate center point between user and destination
    const centerLat = (userLat + destLat) / 2;
    const centerLon = (userLon + destLon) / 2;

    const mapOptions = {
      center: { lat: centerLat, lng: centerLon },
      zoom: 10,
      mapTypeControl: true,
      fullscreenControl: true,
      streetViewControl: false,
    };

    const newMap = new window.google.maps.Map(mapContainer.current, mapOptions);
    setMap(newMap);

    // Add user location marker
    const userMarker = new window.google.maps.Marker({
      position: { lat: userLat, lng: userLon },
      map: newMap,
      title: 'Your Location',
      icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
    });
    userMarkerRef.current = userMarker;

    // Add destination marker
    const destMarker = new window.google.maps.Marker({
      position: { lat: destLat, lng: destLon },
      map: newMap,
      title: destName,
      icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
    });
    destMarkerRef.current = destMarker;

    // Calculate and display route
    calculateRoute(newMap);
  };

  const calculateRoute = (mapInstance) => {
    if (!window.google) return;

    const directionsService = new window.google.maps.DirectionsService();
    const directionsDisplay = new window.google.maps.DirectionsRenderer({
      map: mapInstance,
      suppressMarkers: true, // Don't use default markers, we have our own
      polylineOptions: {
        strokeColor: '#4F46E5',
        strokeOpacity: 0.8,
        strokeWeight: 4,
      },
    });

    const request = {
      origin: { lat: userLat, lng: userLon },
      destination: { lat: destLat, lng: destLon },
      travelMode: window.google.maps.TravelMode.DRIVING,
    };

    directionsService.route(request, (result, status) => {
      if (status === window.google.maps.DirectionsStatus.OK) {
        directionsDisplay.setDirections(result);
        
        // Get route info
        const route = result.routes[0];
        const distance = route.legs[0].distance.text;
        const duration = route.legs[0].duration.text;
        
        setRoute({
          distance,
          duration,
        });
        setError('');
      } else if (status === window.google.maps.DirectionsStatus.ZERO_RESULTS) {
        // Draw simple line if no route found
        const polyline = new window.google.maps.Polyline({
          path: [
            { lat: userLat, lng: userLon },
            { lat: destLat, lng: destLon },
          ],
          geodesic: true,
          strokeColor: '#9333EA',
          strokeOpacity: 0.7,
          strokeWeight: 3,
          map: mapInstance,
        });
        polylineRef.current = polyline;

        // Calculate straight-line distance
        const R = 6371; // Earth's radius in km
        const dLat = (destLat - userLat) * Math.PI / 180;
        const dLon = (destLon - userLon) * Math.PI / 180;
        const a =
          Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(userLat * Math.PI / 180) * Math.cos(destLat * Math.PI / 180) *
          Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = (R * c).toFixed(2);

        setRoute({
          distance: `${distance} km (straight line)`,
          duration: 'N/A',
        });
      } else {
        setError('Unable to calculate route');
      }
      setLoading(false);
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Route to {destName}</h2>
            {route && (
              <div className="mt-2 flex gap-6 text-sm text-gray-600">
                <p>
                  <span className="font-semibold text-gray-900">Distance:</span> {route.distance}
                </p>
                <p>
                  <span className="font-semibold text-gray-900">Duration:</span> {route.duration}
                </p>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Map Container */}
        <div className="flex-1 overflow-hidden bg-gray-100">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-gray-600">Loading route...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full">
              <p className="text-red-600">{error}</p>
            </div>
          )}
          <div
            ref={mapContainer}
            style={{
              width: '100%',
              height: '100%',
              display: loading || error ? 'none' : 'block',
            }}
          />
        </div>

        {/* Legend */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#4285F4' }}></div>
              <span className="text-sm text-gray-700">Your Location</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#EA4335' }}></div>
              <span className="text-sm text-gray-700">Destination</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-1 h-1" style={{ backgroundColor: '#4F46E5' }}></div>
              <div className="w-4 h-0.5" style={{ backgroundColor: '#4F46E5' }}></div>
              <span className="text-sm text-gray-700">Route</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
