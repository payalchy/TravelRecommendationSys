import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const navigate = useNavigate();

  const fetchRecommendations = async () => {
    setLoading(true);
    setError("");

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

      console.log("API RESPONSE:", res.data);

      const data = res.data;

      const results =
        data?.package_results ||
        data?.results ||
        data?.data ||
        data ||
        [];

      setPackages(Array.isArray(results) ? results : []);
    } catch (error) {
      console.log("RECOMMEND ERROR:", error.response?.data || error.message);

      setError(
        error.response?.data?.detail ||
          "Failed to load recommendations"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  return (
    <div style={styles.container}>
      {/* NAVBAR */}
      <div style={styles.navbar}>
        <h2 style={styles.logo}>
          🌍 Personalized Travel Recommendation System
        </h2>

        <div style={styles.navLinks}>
          <span>Home</span>
          <span>Packages</span>
          <span>Wishlist</span>
          <span>Profile</span>
        </div>
      </div>

      {/* HERO */}
      <div style={styles.hero}>
        <h1 style={styles.heroTitle}>PLAN YOUR NEXT TRIP</h1>

        {/* SEARCH */}
        <input
          placeholder="Search destination..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.search}
        />
      </div>

      {/* ERROR */}
      {error && (
        <p style={{ color: "red", textAlign: "center" }}>
          {error}
        </p>
      )}

      {/* CONTENT */}
      <div style={styles.section}>
        <h2 style={{ marginBottom: "20px" }}>
          Recommended Packages
        </h2>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <div style={styles.grid}>
            {packages
              .filter((pkg) =>
                pkg.name
                  ?.toLowerCase()
                  .includes(search.toLowerCase())
              )
              .map((pkg, index) => (
                <div
                  key={pkg.package_id || index}
                  style={styles.card}
                  onClick={() =>
                    navigate(`/package/${pkg.package_id}`)
                  }
                >
                  <img
                    src={
                      pkg.image ||
                      "https://images.unsplash.com/photo-1501785888041-af3ef285b470"
                    }
                    alt={pkg.name || "Package"}
                    style={styles.image}
                  />

                  <div style={styles.overlay}>
                    <h3>{pkg.name}</h3>
                    <p>📍 {pkg.end_location}</p>

                    <div style={styles.badges}>
                      <span>💰 NPR {pkg.budget}</span>
                      <span>⏳ {pkg.duration_days} days</span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
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

  navbar: {
    display: "flex",
    justifyContent: "space-between",
    padding: "20px 40px",
    background: "#111",
    borderBottom: "1px solid #222",
  },

  logo: {
    fontWeight: "bold",
  },

  navLinks: {
    display: "flex",
    gap: "20px",
    color: "#aaa",
  },

  hero: {
    textAlign: "center",
    padding: "60px 20px",
  },

  heroTitle: {
    fontSize: "36px",
    marginBottom: "20px",
  },

  search: {
    padding: "12px",
    width: "300px",
    borderRadius: "8px",
    border: "none",
    background: "#222",
    color: "white",
  },

  section: {
    padding: "20px 40px",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
    gap: "20px",
  },

  card: {
    position: "relative",
    borderRadius: "15px",
    overflow: "hidden",
    cursor: "pointer",
  },

  image: {
    width: "100%",
    height: "260px",
    objectFit: "cover",
  },

  overlay: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    background: "linear-gradient(to top, rgba(0,0,0,0.8), transparent)",
    padding: "15px",
  },

  badges: {
    display: "flex",
    gap: "10px",
    marginTop: "8px",
    fontSize: "12px",
    color: "#ddd",
  },
};