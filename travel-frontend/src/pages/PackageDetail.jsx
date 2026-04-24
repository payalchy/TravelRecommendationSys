import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

export default function PackageDetail() {
  const { id } = useParams();
  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);

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

        const results =
          data?.package_results ||
          data?.results ||
          data?.data ||
          [];

        const found = results.find(
          (p) => p.package_id === parseInt(id)
        );

        setPkg(found || null);
      } catch (err) {
        console.log("DETAIL ERROR:", err.response?.data || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPackage();
  }, [id]);

  if (loading) {
    return (
      <div style={styles.container}>
        <p>Loading package...</p>
      </div>
    );
  }

  if (!pkg) {
    return (
      <div style={styles.container}>
        <p>Package not found</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* HERO */}
      <div style={styles.heroWrapper}>
        <img
          src={
            pkg.image ||
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470"
          }
          style={styles.heroImage}
        />

        <div style={styles.overlay}>
          <h1 style={styles.title}>{pkg.name}</h1>
          <p style={styles.subtitle}>
            📍 {pkg.start_location} → {pkg.end_location}
          </p>
        </div>
      </div>

      {/* CONTENT */}
      <div style={styles.content}>
        {/* DESCRIPTION */}
        <div style={styles.card}>
          <h2>📄 Description</h2>
          <p>{pkg.description}</p>

          <div style={styles.infoRow}>
            <span>💰 {pkg.budget}</span>
            <span>⏳ {pkg.duration_days} days</span>
            <span>📊 {pkg.final_score}</span>
          </div>
        </div>

        {/* ITINERARY */}
        <div style={styles.card}>
          <h2>🗓 Itinerary</h2>

          {pkg.itinerary?.length > 0 ? (
            pkg.itinerary.map((day, i) => (
              <div key={i} style={styles.dayCard}>
                <h3>Day {day.day}</h3>

                <p>
                  <b>{day.destination?.pName}</b>
                </p>

                <img
                  src={
                    day.destination?.image ||
                    "https://via.placeholder.com/600x300"
                  }
                  style={styles.itineraryImage}
                />

                <p>{day.description}</p>
              </div>
            ))
          ) : (
            <p>No itinerary available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

/* STYLES */
const styles = {
  container: {
    background: "#0f0f0f",
    color: "white",
    minHeight: "100vh",
    fontFamily: "sans-serif",
  },

  heroWrapper: {
    position: "relative",
    height: "400px",
  },

  heroImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },

  overlay: {
    position: "absolute",
    bottom: 0,
    padding: "20px",
    background: "linear-gradient(to top, rgba(0,0,0,0.8), transparent)",
    width: "100%",
  },

  title: {
    fontSize: "32px",
  },

  subtitle: {
    color: "#ccc",
  },

  content: {
    padding: "20px 40px",
  },

  card: {
    background: "#111",
    padding: "20px",
    borderRadius: "12px",
    marginBottom: "20px",
  },

  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "10px",
  },

  dayCard: {
    background: "#0a0a0a",
    padding: "15px",
    borderRadius: "10px",
    marginTop: "10px",
  },

  itineraryImage: {
    width: "100%",
    height: "220px",
    objectFit: "cover",
    borderRadius: "10px",
    marginTop: "10px",
  },
};