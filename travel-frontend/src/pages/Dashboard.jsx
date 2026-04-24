import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  // ---------------------------
  // FETCH USER PROFILE
  // ---------------------------
  useEffect(() => {
    const fetchProfile = async () => {
      const token = localStorage.getItem("access");

      try {
        const res = await axios.get(
          "http://127.0.0.1:8000/api/users/profile/",
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        setProfile(res.data);
      } catch (err) {
        console.log(err);
        logout(); // auto logout if token invalid
      }
    };

    fetchProfile();
  }, []);

  // ---------------------------
  // LOGOUT
  // ---------------------------
  const logout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/");
  };

  // ---------------------------
  // GET RECOMMENDATIONS (AI API)
  // ---------------------------
  const getRecommendations = async () => {
    setLoading(true);

    const token = localStorage.getItem("access");

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/recommend/",
        {
          budget: profile.budget,
          season: profile.preferred_season,
          duration: profile.preferred_duration,
          style: profile.preferred_travel_style,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setRecommendations(res.data);
    } catch (err) {
      console.log(err);
      alert("Failed to get recommendations ❌");
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------
  // LOADING STATE
  // ---------------------------
  if (!profile) {
    return <div style={styles.loading}>Loading...</div>;
  }

  return (
    <div style={styles.page}>
      {/* SIDEBAR */}
      <div style={styles.sidebar}>
        <h2 style={styles.logo}>🌍 TravelAI</h2>

        <button style={styles.navBtn}>🏠 Dashboard</button>
        <button style={styles.navBtn}>✈️ Recommendations</button>
        <button style={styles.navBtn}>❤️ Saved Trips</button>

        <button style={styles.logout} onClick={logout}>
          Logout
        </button>
      </div>

      {/* MAIN */}
      <div style={styles.main}>
        <h1 style={styles.title}>
          Welcome, {profile.username}
        </h1>

        {/* CARDS */}
        <div style={styles.grid}>
          <div style={styles.card}>
            💰 <h3>Budget</h3>
            <p>{profile.budget}</p>
          </div>

          <div style={styles.card}>
            🌤 <h3>Season</h3>
            <p>{profile.preferred_season}</p>
          </div>

          <div style={styles.card}>
            📅 <h3>Duration</h3>
            <p>{profile.preferred_duration} days</p>
          </div>
        </div>

        {/* PREFERENCES */}
        <div style={styles.section}>
          <h2>🎯 Travel Preferences</h2>

          <div style={styles.tags}>
            {profile.preferred_travel_style?.map((t, i) => (
              <span key={i} style={styles.tag}>
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* BUTTON */}
        <button
          style={styles.primaryBtn}
          onClick={getRecommendations}
          disabled={loading}
        >
          {loading ? "Finding trips..." : "🚀 Get Recommendations"}
        </button>

        {/* RESULTS */}
        {recommendations.length > 0 && (
          <div style={styles.section}>
            <h2>🌍 Recommended Trips</h2>

            {recommendations.map((item, index) => (
              <div key={index} style={styles.card}>
                <h3>{item.name}</h3>
                <p>{item.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT PANEL */}
      <div style={styles.right}>
        <h3>📌 Quick Info</h3>
        <p>✔ Budget optimized routes</p>
        <p>✔ Personalized destinations</p>
      </div>
    </div>
  );
}
const styles = {
  page: {
    display: "grid",
    gridTemplateColumns: "220px 1fr 250px",
    minHeight: "100vh",
    background: "#0b0b0f",
    color: "white",
    fontFamily: "Arial",
  },

  sidebar: {
    padding: "20px",
    borderRight: "1px solid #222",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },

  logo: {
    color: "#00ffc3",
    marginBottom: "20px",
  },

  navBtn: {
    padding: "10px",
    background: "#111",
    color: "white",
    border: "1px solid #222",
    cursor: "pointer",
    textAlign: "left",
  },

  logout: {
    marginTop: "auto",
    padding: "10px",
    background: "transparent",
    border: "1px solid red",
    color: "red",
    cursor: "pointer",
  },

  main: {
    padding: "30px",
  },

  right: {
    padding: "20px",
    borderLeft: "1px solid #222",
    background: "#0f0f14",
  },

  title: {
    color: "#00ffc3",
    marginBottom: "20px",
  },

  grid: {
    display: "flex",
    gap: "15px",
  },

  card: {
    flex: 1,
    background: "#111",
    padding: "20px",
    borderRadius: "10px",
    border: "1px solid #222",
  },

  section: {
    marginTop: "30px",
    padding: "20px",
    background: "#111",
    borderRadius: "10px",
  },

  tags: {
    display: "flex",
    gap: "10px",
    marginTop: "10px",
  },

  tag: {
    padding: "5px 10px",
    background: "#00ffc3",
    color: "black",
    borderRadius: "20px",
    fontSize: "12px",
  },

  primaryBtn: {
    marginTop: "30px",
    width: "100%",
    padding: "12px",
    background: "linear-gradient(90deg,#00ffc3,#00a6ff)",
    border: "none",
    cursor: "pointer",
    fontWeight: "bold",
  },

  loading: {
    color: "white",
    background: "#000",
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
};