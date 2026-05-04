import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  const [budget, setBudget] = useState("");
  const [duration, setDuration] = useState("");
  const [season, setSeason] = useState("summer");

  const [travelStyles, setTravelStyles] = useState([]);
  const [selected, setSelected] = useState([]);

  //  HISTORY ADDED
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  const navigate = useNavigate();

  // ================= FETCH PROFILE =================
  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem("access");

      const res = await axios.get(
        "http://127.0.0.1:8000/api/users/profile/",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = res.data || {};

      setUsername(data.username || "");
      setEmail(data.email || "");

      setBudget(data.budget ?? "");
      setDuration(data.preferred_duration ?? "");
      setSeason(data.preferred_season || "summer");

      const styles = Array.isArray(data.preferred_travel_style)
        ? data.preferred_travel_style
        : [];

      setSelected(styles.map((s) => s.id));
    } catch (err) {
      console.log("Profile error:", err.response?.data || err.message);
    } finally {
      setPageLoading(false);
    }
  };

  // ================= FETCH STYLES =================
  const fetchTravelStyles = async () => {
    try {
      const res = await axios.get(
        "http://127.0.0.1:8000/api/users/travel-styles/"
      );

      setTravelStyles(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.log("Styles error:", err.message);
    }
  };

  // ================= FETCH HISTORY =================
  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem("access");

      const res = await axios.get(
        "http://127.0.0.1:8000/api/users/profile/history/",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setHistory(Array.isArray(res.data) ? res.data : []);
      setShowHistory(true);
    } catch (err) {
      console.log("History error:", err.response?.data || err.message);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchTravelStyles();
  }, []);

  // ================= TOGGLE STYLE =================
  const toggleStyle = (id) => {
    setSelected((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
    );
  };

  // ================= SAVE PROFILE =================
  const saveProfile = async () => {
    setLoading(true);

    try {
      const token = localStorage.getItem("access");

      await axios.put(
        "http://127.0.0.1:8000/api/users/profile/",
        {
          budget: Number(budget),
          preferred_duration: Number(duration),
          preferred_season: season,
          preferred_travel_style_ids: selected,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      navigate("/home");
    } catch (err) {
      console.log("Save error:", err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) {
    return <div style={styles.loading}>Loading Profile...</div>;
  }

  return (
    <div style={styles.page}>
      {/* LEFT SIDE */}
      <div style={styles.left}>
        <div style={styles.avatar}>✈️</div>

        {/*  CLICK USERNAME FOR HISTORY */}
        <h2 style={styles.name} onClick={fetchHistory}>
          {username || "Guest"}
        </h2>

        <p style={styles.email}>{email}</p>

        <div style={styles.cardSmall}>
          <p>🌍 Travel Profile</p>
          <p>Customize your journey</p>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div style={styles.right}>
        <h1 style={styles.title}>Your Travel Preferences</h1>

        <div style={styles.card}>
          <label>Budget (NPR)</label>
          <input
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            style={styles.input}
            type="number"
          />
        </div>

        <div style={styles.card}>
          <label>Duration (Days)</label>
          <input
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            style={styles.input}
            type="number"
          />
        </div>

        <div style={styles.card}>
          <label>Season</label>
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            style={styles.input}
          >
            <option value="summer">Summer</option>
            <option value="rainy">Rainy</option>
            <option value="spring">Spring</option>
            <option value="autumn">Autumn</option>
            <option value="winter">Winter</option>
          </select>
        </div>

        <div style={styles.card}>
          <label>Travel Styles</label>

          <div style={styles.tags}>
            {travelStyles.map((t) => (
              <span
                key={t.id}
                onClick={() => toggleStyle(t.id)}
                style={{
                  ...styles.tag,
                  background: selected.includes(t.id)
                    ? "#00c896"
                    : "#222",
                }}
              >
                {t.name}
              </span>
            ))}
          </div>
        </div>

        <button onClick={saveProfile} style={styles.button}>
          {loading ? "Saving..." : "Save Profile"}
        </button>
      </div>

      {/* ================= HISTORY MODAL ================= */}
      {showHistory && (
        <div style={styles.modal}>
          <div style={styles.modalBox}>
            <div style={styles.modalHeader}>
              <h3>📜 Travel History</h3>
              <button onClick={() => setShowHistory(false)}>
                Close
              </button>
            </div>

            <div style={styles.historyList}>
              {history.length === 0 ? (
                <p>No history found</p>
              ) : (
                history.map((h) => (
                  <div key={h.id} style={styles.historyCard}>
                    <p>💰 Budget: {h.budget}</p>
                    <p>⏳ Duration: {h.duration}</p>
                    <p>🌤 Season: {h.season}</p>
                    <p>🏷 Styles: {h.travel_styles}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ================= STYLES (YOUR SAME DESIGN + ADDITION) ================= */
const styles = {
  page: {
    display: "flex",
    minHeight: "100vh",
    background: "#0b0f19",
    color: "white",
    fontFamily: "sans-serif",
  },

  left: {
    width: "30%",
    background: "linear-gradient(180deg,#111827,#0b0f19)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px",
  },

  right: {
    width: "70%",
    padding: "40px",
  },

  avatar: {
    fontSize: "60px",
    marginBottom: "10px",
  },

  name: {
    fontSize: "22px",
    marginBottom: "5px",
    cursor: "pointer",
    color: "#00c896",
  },

  email: {
    fontSize: "14px",
    color: "#aaa",
  },

  cardSmall: {
    marginTop: "20px",
    padding: "12px",
    background: "#111827",
    borderRadius: "10px",
    textAlign: "center",
    color: "#aaa",
  },

  title: {
    fontSize: "26px",
    marginBottom: "20px",
  },

  card: {
    background: "#111827",
    padding: "15px",
    borderRadius: "12px",
    marginBottom: "15px",
  },

  input: {
    width: "100%",
    marginTop: "8px",
    padding: "10px",
    borderRadius: "8px",
    border: "none",
    background: "#1f2937",
    color: "white",
  },

  tags: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
    marginTop: "10px",
  },

  tag: {
    padding: "6px 12px",
    borderRadius: "20px",
    cursor: "pointer",
    fontSize: "13px",
  },

  button: {
    width: "100%",
    padding: "12px",
    border: "none",
    borderRadius: "10px",
    background: "#00c896",
    color: "black",
    fontWeight: "bold",
    cursor: "pointer",
  },

  loading: {
    color: "white",
    textAlign: "center",
    marginTop: "50px",
  },

  /* HISTORY */
  modal: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    background: "rgba(0,0,0,0.7)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },

  modalBox: {
    background: "#111827",
    padding: "20px",
    borderRadius: "12px",
    width: "420px",
    maxHeight: "80vh",
    overflowY: "auto",
  },

  modalHeader: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "10px",
  },

  historyList: {
    marginTop: "10px",
  },

  historyCard: {
    background: "#1f2937",
    padding: "10px",
    borderRadius: "10px",
    marginBottom: "10px",
  },
};