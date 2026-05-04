import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useSearchParams } from "react-router-dom";

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
  const [formError, setFormError] = useState("");

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isSetupMode = searchParams.get("setup") === "1";

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
    if (!selected.length) {
      setFormError("Please select at least one travel style.");
      return;
    }

    setFormError("");
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

      if (isSetupMode) {
        navigate("/home?onboarding=1");
      } else {
        navigate("/home");
      }
    } catch (err) {
      console.log("Save error:", err.response?.data || err.message);
      setFormError("Unable to save profile. Please check your values and try again.");
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
        <div style={styles.avatar}>Profile</div>

        {/*  CLICK USERNAME FOR HISTORY */}
        <h2 style={styles.name} onClick={fetchHistory}>
          {username || "Guest"}
        </h2>

        <p style={styles.email}>{email}</p>

        <div style={styles.cardSmall}>
          <p> Travel Profile</p>
          <p>Customize your journey</p>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div style={styles.right}>
        <h1 style={styles.title}>
          {isSetupMode ? "Set Your Travel Preferences" : "Update Your Travel Preferences"}
        </h1>
        <p style={styles.subtitle}>
          {isSetupMode
            ? "Complete this once to continue to Home. You can update this later anytime from Profile settings."
            : "You can update your preferences anytime and save changes."}
        </p>

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
                    ? "#2f6fed"
                    : "#7a879c",
                }}
              >
                {t.name}
              </span>
            ))}
          </div>
        </div>

        <button onClick={saveProfile} style={styles.button}>
          {loading ? "Saving..." : isSetupMode ? "Save And Continue" : "Save "}
        </button>

        {formError && <p style={styles.errorText}>{formError}</p>}
      </div>

      {/* ================= HISTORY MODAL ================= */}
      {showHistory && (
        <div style={styles.modal}>
          <div style={styles.modalBox}>
            <div style={styles.modalHeader}>
              <h3>Travel History</h3>
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
                    <p> Budget: {h.budget}</p>
                    <p> Duration: {h.duration}</p>
                    <p> Season: {h.season}</p>
                    <p> Styles: {h.travel_styles}</p>
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

/* ================= STYLES ================= */
const styles = {
  page: {
    display: "flex",
    flexWrap: "wrap",
    minHeight: "100vh",
    background: "#f7f9fc",
    color: "#1f2a44",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
  },

  left: {
    width: "32%",
    minWidth: "280px",
    background: "#ffffff",
    borderRight: "1px solid #e2e8f4",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "32px 24px",
  },

  right: {
    flex: 1,
    minWidth: "320px",
    padding: "32px 24px",
  },

  avatar: {
    fontSize: "60px",
    marginBottom: "12px",
  },

  name: {
    fontSize: "22px",
    margin: "0 0 6px",
    cursor: "pointer",
    color: "#183b66",
  },

  email: {
    fontSize: "14px",
    color: "#5f6f89",
  },

  cardSmall: {
    marginTop: "20px",
    padding: "12px 14px",
    background: "#f2f7ff",
    border: "1px solid #d5e2fb",
    borderRadius: "10px",
    textAlign: "center",
    color: "#42536f",
  },

  title: {
    fontSize: "26px",
    color: "#1d3557",
    marginBottom: "10px",
  },

  subtitle: {
    color: "#5f6f89",
    marginTop: "0",
    marginBottom: "18px",
    fontSize: "14px",
  },

  card: {
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    boxShadow: "0 6px 18px rgba(24, 59, 102, 0.08)",
    padding: "15px",
    borderRadius: "12px",
    marginBottom: "15px",
  },

  input: {
    width: "100%",
    marginTop: "8px",
    padding: "10px 12px",
    borderRadius: "10px",
    border: "1px solid #cdd8ea",
    background: "#f9fbff",
    color: "#1f2a44",
    outline: "none",
  },

  tags: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
    marginTop: "10px",
  },

  tag: {
    padding: "7px 12px",
    borderRadius: "20px",
    cursor: "pointer",
    fontSize: "13px",
    color: "#ffffff",
  },

  button: {
    width: "100%",
    padding: "12px",
    border: "none",
    borderRadius: "10px",
    background: "#2f6fed",
    color: "#ffffff",
    fontWeight: "600",
    cursor: "pointer",
  },

  errorText: {
    color: "#c0392b",
    marginTop: "12px",
    marginBottom: "0",
    textAlign: "center",
  },

  loading: {
    color: "#1f2a44",
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
    background: "rgba(16, 24, 40, 0.45)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "16px",
  },

  modalBox: {
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    padding: "20px",
    borderRadius: "12px",
    width: "min(520px, 100%)",
    maxHeight: "80vh",
    overflowY: "auto",
  },

  modalHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
  },

  historyList: {
    marginTop: "10px",
  },

  historyCard: {
    background: "#f2f7ff",
    border: "1px solid #d5e2fb",
    padding: "10px",
    borderRadius: "10px",
    marginBottom: "10px",
  },
};