let googleMapsLoader;

function loadGoogleMaps(apiKey) {
  if (window.google && window.google.maps) {
    return Promise.resolve(window.google.maps);
  }

  if (!apiKey) {
    return Promise.reject(new Error('Google Maps API key is missing.'));
  }

  if (!googleMapsLoader) {
    googleMapsLoader = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      const callbackName = '__travelAdminGoogleMapsInit';

      window[callbackName] = () => {
        delete window[callbackName];
        resolve(window.google.maps);
      };

      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&callback=${callbackName}`;
      script.async = true;
      script.defer = true;
      script.onerror = () => {
        delete window[callbackName];
        reject(new Error('Unable to load Google Maps.'));
      };
      document.head.appendChild(script);
    });
  }

  return googleMapsLoader;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-map-picker]').forEach((wrapper) => {
    if (wrapper.dataset.initialized === '1') {
      return;
    }

    const inputId = wrapper.dataset.inputId;
    const input = document.getElementById(inputId);
    const mapElement = wrapper.querySelector('.tm-map-picker__map');
    const selectedName = wrapper.querySelector('[data-selected-name]');
    const clearButton = wrapper.querySelector('[data-clear-selection]');
    const apiKey = wrapper.dataset.googleApiKey || '';
    const searchInput = wrapper.querySelector('[data-search-input]');
    const searchResults = wrapper.querySelector('[data-search-results]');

    if (!input || !mapElement) {
      return;
    }

    let destinations = [];
    try {
      destinations = JSON.parse(wrapper.dataset.destinations || '[]');
    } catch (error) {
      destinations = [];
    }

    const setLabel = (destination) => {
      if (selectedName) {
        selectedName.textContent = destination
          ? `${destination.name}${destination.province ? ` (${destination.province})` : ''}`
          : 'No start location selected';
      }
    };

    const currentSelection = destinations.find((destination) => String(destination.id) === String(input.value));
    setLabel(currentSelection || null);
    const createPinUrl = wrapper.dataset.createPinUrl || '';

    const getCookie = (name) => {
      const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
      return v ? v.pop() : '';
    };

    const createPinnedDestination = (lat, lng) => {
      if (!createPinUrl) return Promise.resolve(null);
      const csrftoken = getCookie('csrftoken');
      return fetch(createPinUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ latitude: lat, longitude: lng }),
      }).then((res) => {
        if (!res.ok) throw new Error('Failed to create pin');
        return res.json();
      });
    };

    // Search functionality using Google Geocoding API
    let searchTimeout = null;
    if (searchInput && apiKey) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();

        if (query.length < 2) {
          searchResults.classList.remove('active');
          searchResults.innerHTML = '';
          return;
        }

        searchTimeout = setTimeout(() => {
          const geocoder = new google.maps.Geocoder();
          
          // Try searching with location bias to Nepal first
          const searchOptions = {
            address: query,
            bounds: new google.maps.LatLngBounds(
              new google.maps.LatLng(26.3, 80.0),
              new google.maps.LatLng(30.4, 88.2)
            ),
            componentRestrictions: { country: 'np' }
          };
          
          geocoder.geocode(searchOptions, (results, status) => {
            if (status === 'OK' && results.length > 0) {
              searchResults.innerHTML = '';
              results.slice(0, 5).forEach((result) => {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'tm-map-picker__search-result';
                resultDiv.innerHTML = `
                  <div class="tm-map-picker__search-result-name">${result.formatted_address}</div>
                  <div class="tm-map-picker__search-result-desc">Lat: ${result.geometry.location.lat().toFixed(4)}, Lng: ${result.geometry.location.lng().toFixed(4)}</div>
                `;
                resultDiv.addEventListener('click', () => {
                  const lat = result.geometry.location.lat();
                  const lng = result.geometry.location.lng();
                  selectLocationFromSearch(lat, lng, result.formatted_address);
                });
                searchResults.appendChild(resultDiv);
              });
              searchResults.classList.add('active');
            } else if (status === 'ZERO_RESULTS') {
              // If no results with Nepal restriction, try broader search
              geocoder.geocode({ address: query + ', Nepal' }, (results2, status2) => {
                if (status2 === 'OK' && results2.length > 0) {
                  searchResults.innerHTML = '';
                  results2.slice(0, 5).forEach((result) => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'tm-map-picker__search-result';
                    resultDiv.innerHTML = `
                      <div class="tm-map-picker__search-result-name">${result.formatted_address}</div>
                      <div class="tm-map-picker__search-result-desc">Lat: ${result.geometry.location.lat().toFixed(4)}, Lng: ${result.geometry.location.lng().toFixed(4)}</div>
                    `;
                    resultDiv.addEventListener('click', () => {
                      const lat = result.geometry.location.lat();
                      const lng = result.geometry.location.lng();
                      selectLocationFromSearch(lat, lng, result.formatted_address);
                    });
                    searchResults.appendChild(resultDiv);
                  });
                  searchResults.classList.add('active');
                } else {
                  searchResults.innerHTML = '<div class="tm-map-picker__search-result" style="color: #6b7280; cursor: default;">No results found</div>';
                  searchResults.classList.add('active');
                }
              });
            } else {
              searchResults.innerHTML = '<div class="tm-map-picker__search-result" style="color: #6b7280; cursor: default;">No results found</div>';
              searchResults.classList.add('active');
            }
          });
        }, 300);
      });

      document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
          searchResults.classList.remove('active');
        }
      });
    }

    const selectLocationFromSearch = (lat, lng, address) => {
      searchInput.value = '';
      searchResults.classList.remove('active');
      searchResults.innerHTML = '';

      // Just display the location without creating a destination
      setLabel({ name: address });
      placeMarker({ lat, lng });
      if (currentMap) {
        currentMap.panTo({ lat, lng });
        currentMap.setZoom(10);
      }
    };

    const nepalCenter = { lat: 28.3949, lng: 84.1240 };

    const haversineDistance = (lat1, lng1, lat2, lng2) => {
      const toRadians = (value) => (value * Math.PI) / 180;
      const earthRadiusKm = 6371;
      const deltaLat = toRadians(lat2 - lat1);
      const deltaLng = toRadians(lng2 - lng1);
      const a =
        Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
          Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
      return 2 * earthRadiusKm * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    };

    const findNearestDestination = (lat, lng) => {
      if (!destinations.length) return null;
      return destinations.reduce((best, dest) => {
        const d = haversineDistance(lat, lng, Number(dest.latitude), Number(dest.longitude));
        if (!best || d < best.d) return { dest, d };
        return best;
      }, null)?.dest || null;
    };

    let setSelection; // Declare here so it can be used in selectLocationFromSearch
    let currentMap = null; // Track current map instance

    const initGoogle = (maps) => {
      const map = new maps.Map(mapElement, {
        center: nepalCenter,
        zoom: 7,
        scrollwheel: true,
        zoomControl: true,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
      });

      currentMap = map;

      const infoWindow = new maps.InfoWindow();
      let activeMarker = null;

      placeMarker = (latLng) => {
        if (!activeMarker) {
          activeMarker = new maps.Marker({
            position: latLng,
            map,
            draggable: false,
            icon: {
              path: maps.SymbolPath.CIRCLE,
              fillColor: '#0f766e',
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 2,
              scale: 10,
            },
          });
        } else {
          activeMarker.setPosition(latLng);
        }
      };

      setSelection = (destination, latLng = null) => {
        input.value = destination ? String(destination.id) : '';
        setLabel(destination);

        if (latLng) {
          placeMarker(latLng);
          map.panTo(latLng);
        }

        if (destination) {
          map.setZoom(10);
          if (!latLng) {
            placeMarker({ lat: destination.latitude, lng: destination.longitude });
            map.panTo({ lat: destination.latitude, lng: destination.longitude });
          }
        }
      };

      if (currentSelection) {
        setSelection(currentSelection, { lat: currentSelection.latitude, lng: currentSelection.longitude });
      }

      map.addListener('click', (event) => {
        const lat = event.latLng.lat();
        const lng = event.latLng.lng();
        placeMarker({ lat, lng });
        // Just display the location without creating a destination
        setLabel({ name: `Location: ${lat.toFixed(5)}, ${lng.toFixed(5)}` });
        infoWindow.setContent(`<strong>${lat.toFixed(5)}, ${lng.toFixed(5)}</strong>`);
        infoWindow.setPosition({ lat, lng });
        infoWindow.open({ map });
      });

      if (clearButton) {
        clearButton.addEventListener('click', () => {
          setSelection(null);
          infoWindow.close();
          if (activeMarker) {
            activeMarker.setMap(null);
            activeMarker = null;
          }
        });
      }

      wrapper.dataset.initialized = '1';
    };

        const loadLeafletLibrary = () => {
          return new Promise((resolve, reject) => {
            if (window.L && window.L.map) {
              resolve();
              return;
            }

            let cssLoaded = false;
            let jsLoaded = false;

            const checkBothLoaded = () => {
              if (cssLoaded && jsLoaded) {
                setTimeout(() => {
                  if (window.L && window.L.map) {
                    resolve();
                  } else {
                    reject(new Error('Leaflet not available'));
                  }
                }, 100);
              }
            };

            // Load Leaflet CSS
            const leafletCss = document.createElement('link');
            leafletCss.rel = 'stylesheet';
            leafletCss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            leafletCss.onload = () => {
              cssLoaded = true;
              checkBothLoaded();
            };
            leafletCss.onerror = () => {
              cssLoaded = true;
              checkBothLoaded();
            };
            document.head.appendChild(leafletCss);

            // Load Leaflet JS
            const leafletJs = document.createElement('script');
            leafletJs.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            leafletJs.onload = () => {
              jsLoaded = true;
              checkBothLoaded();
            };
            leafletJs.onerror = () => {
              reject(new Error('Failed to load Leaflet library'));
            };
            document.head.appendChild(leafletJs);
          });
        };

        const initLeaflet = () => {
          loadLeafletLibrary().then(() => {
            // Ensure map element is visible
            mapElement.style.display = 'block';
            mapElement.style.height = '450px';
            mapElement.style.width = '100%';
            
            const nepalCenter = [28.3949, 84.1240];
            
            try {
              const map = L.map(mapElement).setView(nepalCenter, 7);

              currentMap = { panTo: (latlng) => map.panTo(latlng), setZoom: (z) => map.setZoom(z) };

              // Add tile layer (OpenStreetMap)
              L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19,
              }).addTo(map);

              let activeMarker = null;

              placeMarker = (latlng) => {
                if (!activeMarker) {
                  activeMarker = L.circleMarker(latlng, {
                    radius: 8,
                    color: '#0f766e',
                    weight: 2,
                    fillColor: '#0f766e',
                    fillOpacity: 1,
                  }).addTo(map);
                } else {
                  activeMarker.setLatLng(latlng);
                }
              };

              setSelection = (destination, latlng) => {
                input.value = destination ? String(destination.id) : '';
                setLabel(destination);

                if (latlng) {
                  if (!activeMarker) {
                    activeMarker = L.circleMarker(latlng, {
                      radius: 8,
                      color: '#0f766e',
                      weight: 2,
                      fillColor: '#0f766e',
                      fillOpacity: 1,
                    }).addTo(map);
                  } else {
                    activeMarker.setLatLng(latlng);
                  }
                  map.panTo(latlng);
                }

                if (destination) {
                  map.setZoom(10);
                }
              };

              if (currentSelection) {
                setSelection(currentSelection, [currentSelection.latitude, currentSelection.longitude]);
              }

              // On map click, place a pin and create a Destination at that exact location
              map.on('click', (e) => {
                const lat = e.latlng.lat;
                const lng = e.latlng.lng;
                // Just display the location without creating a destination
                setLabel({ name: `Location: ${lat.toFixed(5)}, ${lng.toFixed(5)}` });
                if (!activeMarker) {
                  activeMarker = L.circleMarker([lat, lng], {
                    radius: 8,
                    color: '#0f766e',
                    weight: 2,
                    fillColor: '#0f766e',
                    fillOpacity: 1,
                  }).addTo(map).bindPopup(`<strong>${lat.toFixed(5)}, ${lng.toFixed(5)}</strong>`).openPopup();
                } else {
                  activeMarker.setLatLng([lat, lng]).bindPopup(`<strong>${lat.toFixed(5)}, ${lng.toFixed(5)}</strong>`).openPopup();
                }
                map.panTo([lat, lng]);
                map.setZoom(10);
              });

              if (clearButton) {
                clearButton.addEventListener('click', () => {
                  setSelection(null);
                  if (activeMarker) {
                    map.removeLayer(activeMarker);
                    activeMarker = null;
                  }
                });
              }

              // Search functionality for Leaflet (using Nominatim API)
              if (searchInput) {
                let searchTimeout = null;
                searchInput.addEventListener('input', (e) => {
                  clearTimeout(searchTimeout);
                  const query = e.target.value.trim();

                  if (query.length < 2) {
                    searchResults.classList.remove('active');
                    searchResults.innerHTML = '';
                    return;
                  }

                  searchTimeout = setTimeout(() => {
                    // Try searching in Nepal context first
                    const nominatimUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&countrycodes=np&format=json&limit=5&bounded=1&viewbox=80.0,26.3,88.2,30.4`;
                    
                    fetch(nominatimUrl, {
                      headers: { 'User-Agent': 'Travel-Admin/1.0' }
                    })
                      .then(res => res.json())
                      .then(results => {
                        if (results.length > 0) {
                          searchResults.innerHTML = '';
                          results.forEach((result) => {
                            const resultDiv = document.createElement('div');
                            resultDiv.className = 'tm-map-picker__search-result';
                            resultDiv.innerHTML = `
                              <div class="tm-map-picker__search-result-name">${result.display_name}</div>
                              <div class="tm-map-picker__search-result-desc">Lat: ${parseFloat(result.lat).toFixed(4)}, Lng: ${parseFloat(result.lon).toFixed(4)}</div>
                            `;
                            resultDiv.addEventListener('click', () => {
                              selectLocationFromSearch(parseFloat(result.lat), parseFloat(result.lon), result.display_name);
                            });
                            searchResults.appendChild(resultDiv);
                          });
                          searchResults.classList.add('active');
                        } else {
                          // If no Nepal-specific results, try broader search
                          const nominatimUrl2 = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query + ', Nepal')}&format=json&limit=5`;
                          fetch(nominatimUrl2, {
                            headers: { 'User-Agent': 'Travel-Admin/1.0' }
                          })
                            .then(res => res.json())
                            .then(results2 => {
                              if (results2.length > 0) {
                                searchResults.innerHTML = '';
                                results2.forEach((result) => {
                                  const resultDiv = document.createElement('div');
                                  resultDiv.className = 'tm-map-picker__search-result';
                                  resultDiv.innerHTML = `
                                    <div class="tm-map-picker__search-result-name">${result.display_name}</div>
                                    <div class="tm-map-picker__search-result-desc">Lat: ${parseFloat(result.lat).toFixed(4)}, Lng: ${parseFloat(result.lon).toFixed(4)}</div>
                                  `;
                                  resultDiv.addEventListener('click', () => {
                                    selectLocationFromSearch(parseFloat(result.lat), parseFloat(result.lon), result.display_name);
                                  });
                                  searchResults.appendChild(resultDiv);
                                });
                                searchResults.classList.add('active');
                              } else {
                                searchResults.innerHTML = '<div class="tm-map-picker__search-result" style="color: #6b7280; cursor: default;">No results found</div>';\n                                searchResults.classList.add('active');
                              }
                            })
                            .catch(err => {
                              console.error('Search error:', err);
                              searchResults.innerHTML = '<div class="tm-map-picker__search-result" style="color: #6b7280; cursor: default;">Search error</div>';\n                              searchResults.classList.add('active');
                            });
                        }
                      })
                      .catch(err => {
                        console.error('Search error:', err);
                        searchResults.innerHTML = '<div class="tm-map-picker__search-result" style="color: #6b7280; cursor: default;">Search error</div>';\n                        searchResults.classList.add('active');
                      });
                  }, 300);
                });
              }

              wrapper.dataset.initialized = '1';
            } catch (e) {
              console.error('Failed to initialize Leaflet map:', e);
              mapElement.innerHTML = '<div class="tm-map-picker__error">Failed to initialize map. Please refresh the page.</div>';
            }
          }).catch((err) => {
            console.error('Failed to load Leaflet:', err);
            mapElement.innerHTML = '<div class="tm-map-picker__error">Could not load map library. Please check your internet connection.</div>';
          });
        };

        // If apiKey exists, try Google first, otherwise use Leaflet
        if (apiKey) {
          loadGoogleMaps(apiKey).then(initGoogle).catch(() => {
            console.log('Google Maps failed, falling back to Leaflet');
            initLeaflet();
          });
        } else {
          console.log('No Google Maps API key, using Leaflet');
          initLeaflet();
        }
  });
});
