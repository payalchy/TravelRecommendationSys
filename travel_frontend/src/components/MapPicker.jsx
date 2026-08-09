import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { resolveLocationSearch } from '../services/api';

export default function MapPicker({ initialLat, initialLon, onLocationSelected, onClose }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  const safeInitialLat = Number.isFinite(Number(initialLat)) && Number(initialLat) >= -90 && Number(initialLat) <= 90
    ? Number(initialLat)
    : 27.7172;
  const safeInitialLon = Number.isFinite(Number(initialLon)) && Number(initialLon) >= -180 && Number(initialLon) <= 180
    ? Number(initialLon)
    : 85.3240;

  const [selectedLat, setSelectedLat] = useState(safeInitialLat);
  const [selectedLon, setSelectedLon] = useState(safeInitialLon);
  const [selectedPlace, setSelectedPlace] = useState('Kathmandu');
  const [searchText, setSearchText] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);

  useEffect(() => {
    if (!mapContainer.current) return;

    // Fix icon URLs (use CDN to avoid bundler issues)
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    });

    const map = L.map(mapContainer.current).setView([safeInitialLat, safeInitialLon], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const marker = L.marker([safeInitialLat, safeInitialLon], { draggable: true }).addTo(map);

    marker.on('dragend', function (e) {
      const { lat, lng } = e.target.getLatLng();
      setSelectedLat(Number(lat));
      setSelectedLon(Number(lng));
      setSelectedPlace('Custom selected location');
    });

    map.on('click', function (e) {
      const { lat, lng } = e.latlng;
      marker.setLatLng([lat, lng]);
      setSelectedLat(Number(lat));
      setSelectedLon(Number(lng));
      setSelectedPlace('Custom selected location');
    });

    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []);

  useEffect(() => {
    // keep marker in sync if initial props change
    if (markerRef.current && initialLat && initialLon) {
      markerRef.current.setLatLng([initialLat, initialLon]);
      mapRef.current?.setView([initialLat, initialLon]);
      setSelectedLat(Number(initialLat));
      setSelectedLon(Number(initialLon));
    }
  }, [initialLat, initialLon]);

  const handleSearch = async (q) => {
    setSearchText(q);
    if (!q || q.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoadingSearch(true);
    try {
      const resolved = await resolveLocationSearch(q, { limit: 12, country: 'Nepal' });
      setSuggestions(resolved);
    } catch (err) {
      console.error('Location search error', err);
      setSuggestions([]);
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleSelectSuggestion = (item) => {
    const lat = Number(item.latitude);
    const lon = Number(item.longitude);
    const displayName = item.display_name || item.name || 'Selected location';

    setSelectedLat(lat);
    setSelectedLon(lon);
    setSelectedPlace(displayName);

    if (markerRef.current) markerRef.current.setLatLng([lat, lon]);
    if (mapRef.current) mapRef.current.setView([lat, lon], 15);
    setSuggestions([]);
    setSearchText(displayName);
  };

  const handleConfirm = () => {
    onLocationSelected(selectedLat, selectedLon);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Choose Your Location</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <div className="p-4">
          <div className="mb-3">
            <input
              value={searchText}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search for a landmark or place"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            {loadingSearch && <div className="text-xs text-gray-500 mt-1">Searching...</div>}
            {suggestions.length > 0 && (
              <ul className="bg-white border border-gray-200 mt-2 max-h-44 overflow-auto rounded-md">
                {suggestions.map((s, idx) => (
                  <li
                    key={idx}
                    onClick={() => handleSelectSuggestion(s)}
                    className="px-3 py-2 cursor-pointer hover:bg-gray-100 text-sm"
                  >
                    {s.display_name}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div ref={mapContainer} style={{ width: '100%', height: '420px' }} className="rounded-md overflow-hidden" />

          <div className="mt-4 p-3 bg-gray-50 rounded-md border border-gray-100">
            <div className="text-sm text-gray-700 mb-1">Selected Location:</div>
            <div className="text-sm font-semibold text-gray-900 mb-1">{selectedPlace || 'Custom selected location'}</div>
            <div className="text-sm text-gray-600">Latitude: <span className="font-medium">{selectedLat?.toFixed(4)}</span> | Longitude: <span className="font-medium">{selectedLon?.toFixed(4)}</span></div>
            <div className="text-xs text-gray-500 mt-2">Click on the map or drag the marker to select a location.</div>
          </div>

          <div className="mt-4 flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 bg-gray-200 rounded-md">Cancel</button>
            <button onClick={handleConfirm} className="px-4 py-2 bg-blue-600 text-white rounded-md">Confirm Location</button>
          </div>
        </div>
      </div>
    </div>
  );
}
