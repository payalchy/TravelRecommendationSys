import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useSearchParams } from "react-router-dom";

export default function Home() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showOnboardingBanner, setShowOnboardingBanner] = useState(false);

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // =====================
  // FETCH RECOMMENDATIONS
  // =====================
  const fetchPackageRecommendations = async () => {
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
        navigate("/profile?setup=1");
        return;
      }

      fetchPackageRecommendations();
    } catch {
      navigate("/profile");
    }
  };

  useEffect(() => {
    checkProfile();
  }, []);

  useEffect(() => {
    if (searchParams.get("onboarding") === "1") {
      setShowOnboardingBanner(true);
      navigate("/home", { replace: true });
    }
  }, [navigate, searchParams]);

  return (
    <div style={styles.page}>
      {/* ================= NAVBAR ================= */}
      <div style={styles.navbar}>
        <h2 style={styles.logo}>Travel Explorer</h2>

        <div style={styles.navLinks}>
          <span style={styles.navItem}>Home</span>
          <span style={styles.navItem}>Packages</span>
          <span
            style={styles.recommendationNavItem}
            onClick={() => navigate("/destinations")}
          >
            Destination Recommendation
          </span>
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

        <button
          type="button"
          onClick={() => navigate("/destinations")}
          style={styles.refreshButton}
        >
          Get Destination Recommendation
        </button>
      </div>

      {/* ERROR */}
      {error && <p style={styles.error}>{error}</p>}

      {showOnboardingBanner && (
        <div style={styles.onboardingBanner}>
          <p style={styles.onboardingText}>
            Profile setup completed. You can update your travel preferences anytime from Profile settings.
          </p>
          <button
            type="button"
            onClick={() => setShowOnboardingBanner(false)}
            style={styles.bannerCloseButton}
          >
            Dismiss
          </button>
        </div>
      )}

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
                    <p>Location: {pkg.end_location}</p>

                    <div style={styles.badges}>
                      <span>Budget: {pkg.budget}</span>
                      <span>Duration: {pkg.duration_days} days</span>
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
    minHeight: "100vh",
    background: "#f7f9fc",
    color: "#1f2a44",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
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
    zIndex: 20,
  },

  logo: {
    margin: 0,
    fontSize: "21px",
    fontWeight: "700",
    color: "#1d3557",
  },

  navLinks: {
    display: "flex",
    gap: "16px",
    alignItems: "center",
    flexWrap: "wrap",
  },

  navItem: {
    color: "#52627c",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "500",
  },

  recommendationNavItem: {
    color: "#ffffff",
    cursor: "pointer",
    border: "1px solid #2f6fed",
    background: "#2f6fed",
    padding: "7px 10px",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "600",
  },

  profile: {
    color: "#2f6fed",
    cursor: "pointer",
    padding: "6px 10px",
    border: "1px solid #bcd0f6",
    borderRadius: "8px",
    fontWeight: "600",
    background: "#f2f7ff",
  },

  hero: {
    textAlign: "center",
    padding: "34px 16px 20px",
  },

  title: {
    fontSize: "34px",
    margin: "0 0 14px",
    color: "#1d3557",
    letterSpacing: "0.3px",
  },

  search: {
    width: "min(420px, 92%)",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1px solid #cdd8ea",
    background: "#ffffff",
    color: "#1f2a44",
    fontSize: "14px",
    outline: "none",
  },

  refreshButton: {
    marginTop: "12px",
    border: "none",
    background: "#2f6fed",
    color: "#ffffff",
    borderRadius: "10px",
    padding: "10px 16px",
    fontWeight: "600",
    cursor: "pointer",
  },

  error: {
    color: "#c0392b",
    textAlign: "center",
    margin: "8px 0",
    fontWeight: "500",
  },

  onboardingBanner: {
    margin: "10px auto 18px",
    width: "min(940px, calc(100% - 24px))",
    background: "#fff7e6",
    border: "1px solid #f2d29c",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
    padding: "12px 14px",
    flexWrap: "wrap",
  },

  onboardingText: {
    margin: 0,
    color: "#6a4c1f",
    fontSize: "14px",
  },

  bannerCloseButton: {
    border: "1px solid #d9b26a",
    background: "#fff",
    color: "#6a4c1f",
    borderRadius: "8px",
    padding: "6px 10px",
    cursor: "pointer",
    fontWeight: "600",
  },

  container: {
    padding: "16px 24px 30px",
  },

  sectionTitle: {
    marginBottom: "14px",
    color: "#1d3557",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: "16px",
  },

  card: {
    borderRadius: "14px",
    overflow: "hidden",
    cursor: "pointer",
    position: "relative",
    border: "1px solid #dde5f2",
    background: "#fff",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
  },

  image: {
    width: "100%",
    height: "220px",
    objectFit: "cover",
  },

  overlay: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    padding: "12px",
    color: "#fff",
    background: "linear-gradient(to top, rgba(23, 33, 56, 0.82), rgba(23, 33, 56, 0.12))",
  },

  badges: {
    display: "flex",
    gap: "10px",
    fontSize: "12px",
    marginTop: "6px",
  },
};