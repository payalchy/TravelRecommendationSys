import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { recommendationAPI } from "../services/api";

export default function PackageDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedDays, setExpandedDays] = useState({});

  const normalizePointList = (value) => {
    if (Array.isArray(value)) {
      return value.map((item) => String(item).trim()).filter(Boolean);
    }

    if (typeof value === 'string') {
      return value
        .split(/\r?\n/)
        .map((item) => String(item).trim())
        .filter(Boolean);
    }

    return [];
  };

  useEffect(() => {
    const fetchPackage = async () => {
      try {
        const res = await recommendationAPI.getRecommendedPackage(id);
        setPkg(res.data || null);
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
          <p style={styles.duration}>{pkg.days} Days</p>
          <p style={styles.price}>Price: NPR {Number(pkg.budget || 0).toLocaleString()} / 1 Pax</p>
          <p style={styles.duration}>Travelers: {pkg.number_of_travelers || 'N/A'}</p>
          <p style={styles.description}>{pkg.description}</p>

          <button
            onClick={() => navigate(`/booking/${pkg.package_id || id}`)}
            style={styles.bookingButton}
          >
            Booking
          </button>

        </div>

        {/* ITINERARY */}
        <div style={styles.itineraryCard}>
          <h2 style={styles.cardTitle}>Itinerary</h2>

          {/* INCLUDES & EXCLUDES */}
          <div style={styles.includesExcludes}>
            <div style={styles.includesBox}>
              <h4 style={styles.includesTitle}>Includes</h4>
              <ul style={styles.includesList}>
                {normalizePointList(pkg.includes).length > 0 ? (
                  normalizePointList(pkg.includes).map((item, idx) => <li key={idx}>{item}</li>)
                ) : (
                  <li>No specific inclusions listed</li>
                )}
              </ul>
            </div>

            <div style={styles.excludesBox}>
              <h4 style={styles.excludesTitle}>Excludes</h4>
              <ul style={styles.excludesList}>
                {normalizePointList(pkg.excludes).length > 0 ? (
                  normalizePointList(pkg.excludes).map((item, idx) => <li key={idx}>{item}</li>)
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
    background: "#eef2ff",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
    color: "#0f172a",
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
    color: "#0f172a",
    fontWeight: "700",
  },

  subtitle: {
    margin: 0,
    color: "#475569",
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
    boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
  },

  heroImage: {
    width: "100%",
    height: "320px",
    objectFit: "cover",
    display: "block",
  },

  infoCard: {
    background: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "12px",
    padding: "20px",
    marginBottom: "24px",
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
  },

  cardTitle: {
    margin: "0 0 8px",
    fontSize: "20px",
    fontWeight: "700",
    color: "#0f172a",
  },

  duration: {
    margin: "0 0 4px",
    fontSize: "14px",
    color: "#475569",
  },

  price: {
    margin: "0 0 12px",
    fontSize: "14px",
    fontWeight: "600",
    color: "#0f766e",
  },

  description: {
    margin: 0,
    fontSize: "14px",
    lineHeight: "1.75",
    color: "#475569",
  },

  bookingButton: {
    marginTop: "16px",
    background: "#16a34a",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    padding: "10px 16px",
    fontWeight: "700",
    cursor: "pointer",
    fontSize: "14px",
  },

  mapButton: {
    marginTop: "12px",
    background: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    padding: "10px 16px",
    fontWeight: "700",
    cursor: "pointer",
    fontSize: "14px",
  },

  itineraryCard: {
    background: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "12px",
    padding: "20px",
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
  },

  includesExcludes: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "14px",
    marginBottom: "20px",
  },

  includesBox: {
    background: "#f8fafc",
    border: "1px solid #cbd5e1",
    borderRadius: "10px",
    padding: "14px",
  },

  includesTitle: {
    margin: "0 0 10px",
    fontSize: "14px",
    fontWeight: "700",
    color: "#0f172a",
  },

  includesList: {
    margin: 0,
    paddingLeft: "20px",
    fontSize: "13px",
    color: "#334155",
    lineHeight: "1.5",
    textAlign: "left",
    listStyleType: "disc",
  },

  excludesBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
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
    paddingLeft: "20px",
    fontSize: "13px",
    color: "#7f1d1d",
    lineHeight: "1.5",
    textAlign: "left",
    listStyleType: "disc",
  },

  timeline: {
    marginBottom: "20px",
  },

  timelineTitle: {
    margin: "0 0 16px",
    fontSize: "16px",
    fontWeight: "600",
    color: "#0f172a",
  },

  timelineItem: {
    marginBottom: "0",
    borderLeft: "2px solid #cbd5e1",
    paddingLeft: "0",
  },

  timelineMarker: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    padding: "12px 14px",
    background: "#ffffff",
    borderBottom: "1px solid #e5e7eb",
    cursor: "pointer",
    transition: "background 0.2s ease",
  },

  markerDot: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    background: "#2563eb",
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
    color: "#0f172a",
  },

  dayText: {
    fontSize: "13px",
    color: "#475569",
    lineHeight: "1.5",
  },

  noData: {
    padding: "12px",
    color: "#475569",
    fontSize: "13px",
  },

  detailsButton: {
    background: "#334155",
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
    background: "#334155",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 16px",
    fontWeight: "600",
    cursor: "pointer",
  },
};