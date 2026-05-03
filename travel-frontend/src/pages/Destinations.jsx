import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Destinations() {
  const [destinations, setDestinations] = useState([]);
  const [travelStyles, setTravelStyles] = useState([]);
  const [selectedStyles, setSelectedStyles] = useState([]);
  const [initialSelectedStyles, setInitialSelectedStyles] = useState([]);
  const [province, setProvince] = useState("");
  const [provinceOptions, setProvinceOptions] = useState([]);
  const [latitudeInput, setLatitudeInput] = useState("");
  const [longitudeInput, setLongitudeInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [savingStyles, setSavingStyles] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [locationStatus, setLocationStatus] = useState("Click refresh to use your current location");

  const navigate = useNavigate();

  const readLastKnownLocation = () => {
    const raw = localStorage.getItem("lastKnownLocation");
    if (!raw) return null;

    try {
      const parsed = JSON.parse(raw);
      if (
        typeof parsed?.user_latitude === "number" &&
        typeof parsed?.user_longitude === "number"
      ) {
        return parsed;
      }
    } catch {
      return null;
    }

    return null;
  };

  const toggleStyle = (styleId) => {
    setSelectedStyles((prev) =>
      prev.includes(styleId) ? prev.filter((id) => id !== styleId) : [...prev, styleId]
    );
  };

  const hasStyleChanged = () => {
    if (selectedStyles.length !== initialSelectedStyles.length) return true;
    const current = [...selectedStyles].sort((a, b) => a - b);
    const initial = [...initialSelectedStyles].sort((a, b) => a - b);
    return current.some((value, index) => value !== initial[index]);
  };

  const saveTravelStyleUpdateIfNeeded = async (token) => {
    if (!selectedStyles.length) {
      setFormError("Please keep at least one travel style selected.");
      return false;
    }

    if (!hasStyleChanged()) return true;

    setSavingStyles(true);
    try {
      await axios.put(
        "http://127.0.0.1:8000/api/users/profile/",
        { preferred_travel_style_ids: selectedStyles },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setInitialSelectedStyles([...selectedStyles]);
      setFormError("");
      return true;
    } catch {
      setFormError("Could not update travel style. Please try again.");
      return false;
    } finally {
      setSavingStyles(false);
    }
  };

  const getCurrentLocation = () =>
    new Promise((resolve) => {
      if (!navigator.geolocation) {
        const lastKnown = readLastKnownLocation();
        if (lastKnown) {
          setLocationStatus("Geolocation unavailable, using last saved location");
          resolve(lastKnown);
          return;
        }
        setLocationStatus("Geolocation unavailable, using profile location");
        resolve(null);
        return;
      }

      setLocationStatus("Getting your current location...");
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = {
            user_latitude: position.coords.latitude,
            user_longitude: position.coords.longitude,
          };
          localStorage.setItem("lastKnownLocation", JSON.stringify(coords));
          setLatitudeInput(String(coords.user_latitude));
          setLongitudeInput(String(coords.user_longitude));
          setLocationStatus("Using your live location");
          resolve(coords);
        },
        () => {
          const lastKnown = readLastKnownLocation();
          if (lastKnown) {
            setLocationStatus("Live location denied, using last saved location");
            resolve(lastKnown);
            return;
          }
          setLocationStatus("Location denied, using profile location");
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
      );
    });

  const applyLiveLocation = async () => {
    await getCurrentLocation();
  };

  const buildLocationPayload = async () => {
    const lat = Number(latitudeInput);
    const lon = Number(longitudeInput);

    if (latitudeInput !== "" || longitudeInput !== "") {
      if (Number.isNaN(lat) || Number.isNaN(lon)) {
        setFormError("Current location must include valid numeric latitude and longitude.");
        return null;
      }
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        setFormError("Latitude must be between -90 and 90, longitude between -180 and 180.");
        return null;
      }
      setLocationStatus("Using manual location values");
      return { user_latitude: lat, user_longitude: lon };
    }

    return getCurrentLocation();
  };

  const fetchTopDestinations = async () => {
    setLoading(true);
    setError("");
    setFormError("");

    try {
      const token = localStorage.getItem("access");
      const styleSaved = await saveTravelStyleUpdateIfNeeded(token);
      if (!styleSaved) {
        setLoading(false);
        return;
      }

      const locationPayload = await buildLocationPayload();
      if (locationPayload === null) {
        setLoading(false);
        return;
      }

      const payload = { ...(locationPayload || {}) };
      if (province) payload.preferred_province = province;

      const res = await axios.post("http://127.0.0.1:8000/api/recommend/", payload, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const destinationResults = res.data?.destination_results || [];
      setDestinations(destinationResults.slice(0, 5));
    } catch {
      setError("Failed to fetch destination recommendations");
      setLocationStatus("Unable to fetch recommendations");
    } finally {
      setLoading(false);
    }
  };

  const fetchTravelStyles = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/users/travel-styles/");
      setTravelStyles(Array.isArray(res.data) ? res.data : []);
    } catch {
      setTravelStyles([]);
    }
  };

  const fetchProvinceOptions = async (token) => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/destination/provinces/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProvinceOptions(Array.isArray(res.data?.provinces) ? res.data.provinces : []);
    } catch {
      setProvinceOptions([]);
    }
  };

  const checkProfile = async () => {
    try {
      const token = localStorage.getItem("access");
      if (!token) {
        navigate("/");
        return;
      }

      const res = await axios.get("http://127.0.0.1:8000/api/users/profile/", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const p = res.data;
      if (!p?.budget || !p?.preferred_duration || !p?.preferred_travel_style?.length) {
        navigate("/profile?setup=1");
        return;
      }

      const profileStyles = (p.preferred_travel_style || []).map((style) => style.id);
      setSelectedStyles(profileStyles);
      setInitialSelectedStyles(profileStyles);

      if (typeof p.latitude === "number") setLatitudeInput(String(p.latitude));
      if (typeof p.longitude === "number") setLongitudeInput(String(p.longitude));

      fetchProvinceOptions(token);
      fetchTopDestinations();
    } catch {
      navigate("/profile");
    }
  };

  useEffect(() => {
    fetchTravelStyles();
    checkProfile();
  }, []);

  return (
    <div style={styles.page}>
      <div style={styles.navbar}>
        <h2 style={styles.logo}>Top Destination Recommendation</h2>
        <div style={styles.actions}>
          <button type="button" style={styles.actionButton} onClick={() => navigate("/home")}>
            Back To Home
          </button>
        </div>
      </div>

      {error && <p style={styles.error}>{error}</p>}
      {formError && <p style={styles.error}>{formError}</p>}
      <p style={styles.locationStatus}>{locationStatus}</p>

      <div style={styles.formCard}>
        <h3 style={styles.formTitle}>Recommendation Inputs</h3>
        <div style={styles.formGrid}>
          <div>
            <label style={styles.label}>Current Latitude</label>
            <input value={latitudeInput} onChange={(e) => setLatitudeInput(e.target.value)} style={styles.input} placeholder="e.g. 27.7172" />
          </div>
          <div>
            <label style={styles.label}>Current Longitude</label>
            <input value={longitudeInput} onChange={(e) => setLongitudeInput(e.target.value)} style={styles.input} placeholder="e.g. 85.3240" />
          </div>
          <div>
            <label style={styles.label}>Preferred Province (Optional)</label>
            <select value={province} onChange={(e) => setProvince(e.target.value)} style={styles.input}>
              <option value="">All Provinces</option>
              {provinceOptions.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={styles.travelStyleWrap}>
          <label style={styles.label}>Preferred Travel Style</label>
          <div style={styles.styleTags}>
            {travelStyles.map((style) => (
              <button
                key={style.id}
                type="button"
                style={{ ...styles.styleTag, ...(selectedStyles.includes(style.id) ? styles.styleTagActive : {}) }}
                onClick={() => toggleStyle(style.id)}
              >
                {style.name}
              </button>
            ))}
          </div>
        </div>

        <div style={styles.formActions}>
          <button type="button" style={styles.actionButton} onClick={applyLiveLocation} disabled={loading || savingStyles}>
            Use Live Location
          </button>
          <button
            type="button"
            style={{ ...styles.actionButton, ...styles.refreshButton, opacity: loading || savingStyles ? 0.7 : 1 }}
            onClick={fetchTopDestinations}
            disabled={loading || savingStyles}
          >
            {loading ? "Refreshing..." : savingStyles ? "Saving Style..." : "Get Recommendations"}
          </button>
        </div>
      </div>

      {loading ? (
        <p style={styles.loadingText}>Loading nearest destinations...</p>
      ) : (
        <div style={styles.listWrap}>
          {destinations.length === 0 ? (
            <p style={styles.emptyText}>No destination recommendations found.</p>
          ) : (
            destinations.map((destination, index) => (
              <div key={destination.destination_id} style={styles.card}>
                <div style={styles.rank}>{index + 1}</div>
                <div style={styles.cardBody}>
                  <h3 style={styles.name}>{destination.name} ({destination.province})</h3>
                  <p style={styles.meta}>Distance: {Number(destination.distance_km).toFixed(2)} km</p>
                  <p style={styles.meta}>Final score: {Number(destination.final_score).toFixed(3)}</p>
                  <p style={styles.meta}>Preference score: {Number(destination.preference_score).toFixed(3)}</p>
                  {destination.latitude != null && destination.longitude != null && (
                    <a
                      href={`https://www.openstreetmap.org/?mlat=${Number(destination.latitude)}&mlon=${Number(destination.longitude)}#map=11/${Number(destination.latitude)}/${Number(destination.longitude)}`}
                      target="_blank"
                      rel="noreferrer"
                      style={styles.mapLink}
                    >
                      View on map
                    </a>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f7f9fc",
    color: "#1f2a44",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
    paddingBottom: "30px",
  },
  navbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #e2e8f4",
    padding: "14px 24px",
    gap: "12px",
    flexWrap: "wrap",
    background: "#ffffff",
    position: "sticky",
    top: 0,
    zIndex: 20,
  },
  logo: {
    margin: 0,
    fontSize: "22px",
    color: "#1d3557",
  },
  actions: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  },
  actionButton: {
    border: "1px solid #bcd0f6",
    borderRadius: "10px",
    background: "#f2f7ff",
    color: "#2f6fed",
    padding: "10px 14px",
    fontWeight: "600",
    cursor: "pointer",
  },
  refreshButton: {
    background: "#2f6fed",
    border: "1px solid #2f6fed",
    color: "#ffffff",
  },
  error: {
    color: "#c0392b",
    textAlign: "center",
    marginTop: "14px",
    fontWeight: "500",
  },
  locationStatus: {
    color: "#5f6f89",
    textAlign: "center",
    marginTop: "14px",
  },
  formCard: {
    maxWidth: "940px",
    margin: "16px auto 0",
    padding: "16px",
    borderRadius: "12px",
    border: "1px solid #dbe4f0",
    background: "#ffffff",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
  },
  formTitle: {
    margin: "0 0 12px",
    fontSize: "18px",
    color: "#1d3557",
  },
  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "10px",
  },
  label: {
    display: "block",
    fontSize: "13px",
    color: "#52627c",
    marginBottom: "6px",
  },
  input: {
    width: "100%",
    border: "1px solid #cdd8ea",
    borderRadius: "10px",
    background: "#f9fbff",
    color: "#1f2a44",
    padding: "10px",
    boxSizing: "border-box",
    outline: "none",
  },
  travelStyleWrap: {
    marginTop: "12px",
  },
  styleTags: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
  },
  styleTag: {
    border: "1px solid #c5d3ea",
    borderRadius: "999px",
    background: "#eef3fb",
    color: "#52627c",
    padding: "6px 12px",
    cursor: "pointer",
    fontSize: "13px",
  },
  styleTagActive: {
    border: "1px solid #2f6fed",
    background: "#2f6fed",
    color: "#ffffff",
  },
  formActions: {
    marginTop: "12px",
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  },
  loadingText: {
    textAlign: "center",
    marginTop: "24px",
    color: "#52627c",
  },
  listWrap: {
    maxWidth: "940px",
    margin: "22px auto 0",
    padding: "0 20px",
    display: "grid",
    gap: "14px",
  },
  emptyText: {
    textAlign: "center",
    color: "#5f6f89",
  },
  card: {
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    borderRadius: "12px",
    padding: "14px",
    display: "flex",
    gap: "12px",
    alignItems: "flex-start",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
  },
  rank: {
    minWidth: "34px",
    height: "34px",
    borderRadius: "50%",
    background: "#2f6fed",
    color: "#ffffff",
    display: "grid",
    placeItems: "center",
    fontWeight: "700",
  },
  cardBody: {
    flex: 1,
  },
  name: {
    margin: "0 0 8px",
    fontSize: "20px",
    color: "#1d3557",
  },
  meta: {
    margin: "0 0 4px",
    color: "#5f6f89",
  },
  mapLink: {
    display: "inline-block",
    marginTop: "8px",
    color: "#2f6fed",
    textDecoration: "none",
    fontWeight: "600",
  },
};
