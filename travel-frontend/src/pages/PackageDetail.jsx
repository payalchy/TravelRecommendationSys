import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import RouteMap from "../components/RouteMap";

export default function PackageDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedDays, setExpandedDays] = useState({});
  const [actualDistance, setActualDistance] = useState(null);

  useEffect(() => {
    const fetchPackage = async () => {
      try {
        const token = localStorage.getItem("access");

        const res = await axios.post(
          "http://127.0.0.1:8000/api/recommend/",
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = res.data;
        const results = data?.package_results || data?.results || data?.data || [];
        const found = results.find((p) => p.package_id === parseInt(id));

        setPkg(found || null);
      } catch (err) {
        console.log("DETAIL ERROR:", err.response?.data || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPackage();
  }, [id]);

  const toggleDay = (dayNum) => {
    setExpandedDays((prev) => ({
      ...prev,
      [dayNum]: !prev[dayNum],
    }));
  };

  const handleDistanceCalculated = (distance) => {
    setActualDistance(distance);
  };

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.loadingContainer}>
          <p>Loading package...</p>
        </div>
      </div>
    );
  }

  if (!pkg) {
    return (
      <div style={styles.page}>
        <div style={styles.loadingContainer}>
          <p>Package not found</p>
          <button onClick={() => navigate("/home")} style={styles.backButton}>
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      {/* NAVBAR */}
      <div style={styles.navbar}>
        <h2 style={styles.logo}>Travel Package Details</h2>
        <button
          style={styles.backNavButton}
          onClick={() => navigate("/home")}
        >
          ← Back
        </button>
      </div>

      {/* TITLE SECTION */}
      <div style={styles.titleSection}>
        <h1 style={styles.mainTitle}>{pkg.name}</h1>
        <p style={styles.subtitle}>
          {pkg.start_location} to {pkg.end_location}
        </p>
      </div>

      {/* CONTENT */}
      <div style={styles.container}>
        {/* HERO IMAGE */}
        <div style={styles.heroSection}>
          <img
            src={
              pkg.image ||
              "https://images.unsplash.com/photo-1501785888041-af3ef285b470"
            }
            style={styles.heroImage}
            alt={pkg.name}
          />
        </div>

        {/* PACKAGE INFO */}
        <div style={styles.infoCard}>
          <h2 style={styles.cardTitle}>{pkg.name}</h2>
          <div style={styles.infoRow}>
            <p style={styles.duration}>{pkg.duration_days} Days</p>
            {actualDistance && <p style={styles.distance}>Distance: {actualDistance.toFixed(2)} km</p>}
            {!actualDistance && pkg.distance && <p style={styles.distance}>Distance: {pkg.distance.toFixed(2)} km</p>}
          </div>
          <p style={styles.price}>Price: INR {pkg.budget.toLocaleString()} / 1 Pax</p>
          <p style={styles.description}>{pkg.description}</p>
        </div>

        {/* ITINERARY */}
        <div style={styles.itineraryCard}>
          <h2 style={styles.cardTitle}>Itinerary</h2>

          {/* ROUTE MAP */}
          {pkg.start_location && pkg.end_location && pkg.start_coords && pkg.end_coords && (
            <RouteMap
              startLocation={pkg.start_location}
              endLocation={pkg.end_location}
              startCoords={[pkg.start_coords.lat, pkg.start_coords.lng]}
              endCoords={[pkg.end_coords.lat, pkg.end_coords.lng]}
              itinerary={pkg.itinerary || []}
              onDistanceCalculated={handleDistanceCalculated}
            />
          )}

          {/* INCLUDES & EXCLUDES */}
          <div style={styles.includesExcludes}>
            <div style={styles.includesBox}>
              <h4 style={styles.includesTitle}>Includes</h4>
              <ul style={styles.includesList}>
                {pkg.includes && pkg.includes.length > 0 ? (
                  pkg.includes.map((item, idx) => <li key={idx}>{item}</li>)
                ) : (
                  <li>No specific inclusions listed</li>
                )}
              </ul>
            </div>

            <div style={styles.excludesBox}>
              <h4 style={styles.excludesTitle}>Excludes</h4>
              <ul style={styles.excludesList}>
                {pkg.excludes && pkg.excludes.length > 0 ? (
                  pkg.excludes.map((item, idx) => <li key={idx}>{item}</li>)
                ) : (
                  <li>No specific exclusions listed</li>
                )}
              </ul>
            </div>
          </div>

          {/* TIMELINE */}
          <div style={styles.timeline}>
            <h3 style={styles.timelineTitle}>📍 Detailed Itinerary</h3>

            {pkg.itinerary?.length > 0 ? (
              pkg.itinerary.map((day, index) => (
                <div key={index} style={styles.timelineItem}>
                  <div style={styles.timelineMarker}>
                    <div style={styles.markerDot}></div>
                    <div style={styles.dayInfo}>
                      <span style={styles.dayLabel}>
                        Day {day.day_number}
                      </span>
                      <span style={styles.dayText}>
                        {day.destination}{day.description ? ` - ${day.description}` : ""}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p style={styles.noData}>No itinerary available</p>
            )}
          </div>

          {/* DETAILS ALL BUTTON */}
          <button style={styles.detailsButton}>Details All</button>
        </div>
      </div>
    </div>
  );
}

/* ===================== STYLES ===================== */
const styles = {
  page: {
    minHeight: "100vh",
    background: "#f7f9fc",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
    color: "#1f2a44",
  },

  navbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 24px",
    borderBottom: "1px solid #e2e8f4",
    background: "#ffffff",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },

  logo: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "700",
    color: "#1d3557",
  },

  backNavButton: {
    background: "#f2f7ff",
    color: "#2f6fed",
    border: "1px solid #bcd0f6",
    borderRadius: "8px",
    padding: "8px 14px",
    fontWeight: "600",
    cursor: "pointer",
    fontSize: "13px",
  },

  titleSection: {
    textAlign: "center",
    padding: "24px 16px",
    background: "#ffffff",
    borderBottom: "1px solid #e2e8f4",
  },

  mainTitle: {
    margin: "0 0 6px",
    fontSize: "28px",
    color: "#1d3557",
    fontWeight: "700",
  },

  subtitle: {
    margin: 0,
    color: "#52627c",
    fontSize: "14px",
  },

  container: {
    maxWidth: "940px",
    margin: "0 auto",
    padding: "24px 16px",
  },

  heroSection: {
    marginBottom: "24px",
    borderRadius: "12px",
    overflow: "hidden",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.1)",
  },

  heroImage: {
    width: "100%",
    height: "320px",
    objectFit: "cover",
    display: "block",
  },

  infoCard: {
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    borderRadius: "12px",
    padding: "20px",
    marginBottom: "24px",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
  },

  cardTitle: {
    margin: "0 0 8px",
    fontSize: "20px",
    fontWeight: "700",
    color: "#1d3557",
  },

  infoRow: {
    display: "flex",
    gap: "24px",
    marginBottom: "8px",
  },

  duration: {
    margin: 0,
    fontSize: "14px",
    color: "#52627c",
  },

  distance: {
    margin: 0,
    fontSize: "14px",
    color: "#52627c",
  },

  price: {
    margin: "0 0 12px",
    fontSize: "14px",
    fontWeight: "600",
    color: "#2f6fed",
  },

  description: {
    margin: 0,
    fontSize: "14px",
    lineHeight: "1.6",
    color: "#52627c",
  },

  itineraryCard: {
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    borderRadius: "12px",
    padding: "20px",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
  },

  includesExcludes: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "14px",
    marginBottom: "20px",
  },

  includesBox: {
    background: "#f0fdf4",
    border: "1px solid #86efac",
    borderRadius: "10px",
    padding: "14px",
  },

  includesTitle: {
    margin: "0 0 10px",
    fontSize: "14px",
    fontWeight: "700",
    color: "#15803d",
  },

  includesList: {
    margin: 0,
    paddingLeft: "18px",
    fontSize: "13px",
    color: "#166534",
    lineHeight: "1.5",
    textAlign: "left",
  },

  excludesBox: {
    background: "#fef2f2",
    border: "1px solid #fca5a5",
    borderRadius: "10px",
    padding: "14px",
  },

  excludesTitle: {
    margin: "0 0 10px",
    fontSize: "14px",
    fontWeight: "700",
    color: "#991b1b",
  },

  excludesList: {
    margin: 0,
    paddingLeft: "18px",
    fontSize: "13px",
    color: "#7f1d1d",
    lineHeight: "1.5",
    textAlign: "left",
  },

  timeline: {
    marginBottom: "20px",
  },

  timelineTitle: {
    margin: "0 0 16px",
    fontSize: "16px",
    fontWeight: "600",
    color: "#1d3557",
  },

  timelineItem: {
    marginBottom: "0",
    borderLeft: "2px solid #bcd0f6",
    paddingLeft: "0",
  },

  timelineMarker: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    padding: "12px 14px",
    background: "#f9fbff",
    borderBottom: "1px solid #e2e8f4",
    cursor: "pointer",
    transition: "background 0.2s ease",
  },

  markerDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: "#2f6fed",
    marginLeft: "-7px",
    marginTop: "2px",
    flexShrink: 0,
  },

  dayInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    flex: 1,
  },

  dayLabel: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#1d3557",
  },

  dayText: {
    fontSize: "13px",
    color: "#52627c",
    lineHeight: "1.5",
  },

  noData: {
    padding: "12px",
    color: "#52627c",
    fontSize: "13px",
  },

  detailsButton: {
    background: "#2f6fed",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    padding: "12px 24px",
    fontWeight: "600",
    fontSize: "14px",
    cursor: "pointer",
    width: "100%",
    marginTop: "16px",
    transition: "background 0.2s ease",
  },

  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "400px",
    gap: "16px",
  },

  backButton: {
    background: "#2f6fed",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 16px",
    fontWeight: "600",
    cursor: "pointer",
  },
};