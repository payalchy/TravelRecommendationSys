import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const navigate = useNavigate();

  // =====================
  // FETCH RECOMMENDATIONS
  // =====================
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

      const results =
        res.data?.package_results ||
        res.data?.results ||
        res.data?.data ||
        [];

      setPackages(results);
    } catch (err) {
      setError("Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  // =====================
  // CHECK PROFILE
  // =====================
  const checkProfile = async () => {
    try {
      const token = localStorage.getItem("access");

      if (!token) return navigate("/");

      const res = await axios.get(
        "http://127.0.0.1:8000/api/users/profile/",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const p = res.data;

      if (
        !p?.budget ||
        !p?.preferred_duration ||
        !p?.preferred_travel_style?.length
      ) {
        navigate("/profile");
        return;
      }

      fetchRecommendations();
    } catch {
      navigate("/profile");
    }
  };

  useEffect(() => {
    checkProfile();
  }, []);

  return (
    <div style={styles.page}>
      {/* ================= NAVBAR ================= */}
      <div style={styles.navbar}>
        <h2 style={styles.logo}>🌍 Travel Explorer</h2>

        <div style={styles.navLinks}>
          <span style={styles.navItem}>Home</span>
          <span style={styles.navItem}>Packages</span>
          <span style={styles.navItem}>Wishlist</span>

          {/* PROFILE (FIXED from Payal) */}
          <span
            style={styles.profile}
            onClick={() => navigate("/profile")}
          >
            Profile
          </span>
        </div>
      </div>

      {/* ================= HERO ================= */}
      <div style={styles.hero}>
        <h1 style={styles.title}>PLAN YOUR NEXT TRIP</h1>

        <input
          placeholder="Search destination..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.search}
        />
      </div>

      {/* ERROR */}
      {error && <p style={styles.error}>{error}</p>}

      {/* ================= CONTENT ================= */}
      <div style={styles.container}>
        <h2 style={styles.sectionTitle}>Recommended Packages</h2>

        {loading ? (
          <p style={{ textAlign: "center" }}>Loading...</p>
        ) : (
          <div style={styles.grid}>
            {packages
              .filter((p) =>
                p.name?.toLowerCase().includes(search.toLowerCase())
              )
              .map((pkg) => (
                <div
                  key={pkg.package_id}
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
                    style={styles.image}
                  />

                  <div style={styles.overlay}>
                    <h3>{pkg.name}</h3>
                    <p>📍 {pkg.end_location}</p>

                    <div style={styles.badges}>
                      <span>💰 {pkg.budget}</span>
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

/* ===================== STYLES ===================== */
const styles = {
  page: {
    background: "#0f0f0f",
    minHeight: "100vh",
    color: "white",
    fontFamily: "sans-serif",
  },

  navbar: {
    display: "flex",
    justifyContent: "space-between",
    padding: "20px 40px",
    borderBottom: "1px solid #222",
    background: "#111",
  },

  logo: {
    fontWeight: "bold",
  },

  navLinks: {
    display: "flex",
    gap: "25px",
    alignItems: "center",
  },

  navItem: {
    color: "#aaa",
    cursor: "pointer",
  },

  profile: {
    color: "#fff",
    cursor: "pointer",
    padding: "6px 12px",
    border: "1px solid #4caf50",
    borderRadius: "8px",
    transition: "0.3s",
  },

  hero: {
    textAlign: "center",
    padding: "60px 20px",
  },

  title: {
    fontSize: "36px",
    marginBottom: "20px",
  },

  search: {
    padding: "12px",
    width: "320px",
    borderRadius: "10px",
    border: "none",
    background: "#222",
    color: "white",
  },

  error: {
    color: "red",
    textAlign: "center",
  },

  container: {
    padding: "20px 40px",
  },

  sectionTitle: {
    marginBottom: "20px",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
    gap: "20px",
  },

  card: {
    borderRadius: "15px",
    overflow: "hidden",
    cursor: "pointer",
    position: "relative",
    transition: "0.3s",
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
    padding: "15px",
    background: "linear-gradient(to top, rgba(0,0,0,0.8), transparent)",
  },

  badges: {
    display: "flex",
    gap: "10px",
    fontSize: "12px",
    marginTop: "5px",
  },
};