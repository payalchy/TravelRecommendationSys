import { useEffect, useState } from "react";

export default function RouteMap({ startLocation, endLocation, startCoords, endCoords, itinerary = [] }) {
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [roadDistance, setRoadDistance] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!startCoords || !endCoords) return;

    const fetchRoute = async () => {
      setLoading(true);
      setError(null);
      try {
        // Build waypoints array: start -> all itinerary destinations -> end
        const waypoints = [];

        // Add start location
        waypoints.push([startCoords[1], startCoords[0]]); // [lng, lat]

        // Add itinerary destinations in order
        if (itinerary && itinerary.length > 0) {
          itinerary.forEach((day) => {
            if (day.coords) {
              waypoints.push([day.coords.lng, day.coords.lat]);
            }
          });
        }

        // Add end location
        waypoints.push([endCoords[1], endCoords[0]]); // [lng, lat]

        // Build OSRM URL with all waypoints
        const waypointString = waypoints.map((wp) => wp[0] + "," + wp[1]).join(";");
        const url = `https://router.project-osrm.org/route/v1/driving/${waypointString}?overview=full&geometries=geojson`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.routes && data.routes.length > 0) {
          const route = data.routes[0];
          const distanceKm = route.distance / 1000;
          const durationMins = route.duration / 60;

          setRouteData({
            geometry: route.geometry.coordinates,
            distance: distanceKm,
            duration: durationMins,
          });
          setRoadDistance(distanceKm);
        } else if (data.code === "NoRoute") {
          setError("No route found between locations. Check coordinates.");
        } else {
          setError("Unable to calculate route");
        }
      } catch (err) {
        console.error("OSRM Error:", err);
        setError("Error calculating route. Check internet connection.");
      } finally {
        setLoading(false);
      }
    };

    fetchRoute();
  }, [startCoords, endCoords, itinerary]);

  if (!startCoords || !endCoords) {
    return <div style={{ padding: "12px", color: "#52627c", fontSize: "13px" }}>Missing location coordinates</div>;
  }

  // Generate Google Maps directions URL
  const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${startCoords[0]},${startCoords[1]}&destination=${endCoords[0]},${endCoords[1]}&travelmode=driving`;

  return (
    <div style={{ marginBottom: "20px" }}>
      {/* Simple Map Preview */}
      <div style={{ height: "300px", borderRadius: "10px", overflow: "hidden", marginBottom: "12px", background: "#f0f7ff", border: "1px solid #bcd0f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <a
          href={googleMapsUrl}
          target="_blank"
          rel="noreferrer"
          style={{
            textAlign: "center",
            textDecoration: "none",
            color: "#2f6fed",
          }}
        >
          <div style={{ fontSize: "14px", fontWeight: "600", marginBottom: "8px" }}>
            📍 View in Google Maps
          </div>
          <div style={{ fontSize: "12px", color: "#52627c" }}>
            {startLocation} → {endLocation}
          </div>
          <div style={{ fontSize: "11px", color: "#52627c", marginTop: "4px" }}>
            Click to open directions with route path
          </div>
        </a>
      </div>

      {/* Distance Info */}
      {loading && <p style={{ fontSize: "13px", color: "#52627c" }}>Calculating actual route distance...</p>}

      {error && <p style={{ fontSize: "13px", color: "#dc2626" }}>{error}</p>}

      {roadDistance && (
        <div
          style={{
            background: "#f0f7ff",
            border: "1px solid #bcd0f6",
            borderRadius: "8px",
            padding: "12px",
            fontSize: "13px",
            color: "#1d3557",
          }}
        >
          <div>
            <strong>📍 Actual Route Distance:</strong> {roadDistance.toFixed(2)} km
          </div>
          {routeData?.duration && (
            <div style={{ marginTop: "6px", color: "#52627c" }}>
              <strong>⏱️ Estimated Travel Time:</strong> {(routeData.duration / 60).toFixed(1)} hours
            </div>
          )}
          {itinerary && itinerary.length > 0 && (
            <div style={{ marginTop: "6px", color: "#52627c", fontSize: "12px" }}>
              <em>Route includes {itinerary.length} destination(s)</em>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
