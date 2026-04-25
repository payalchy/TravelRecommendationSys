import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/token/",
        {
          username: form.username,
          password: form.password,
        }
      );

      //  DEBUG (IMPORTANT FOR YOUR ERROR)
      console.log("LOGIN RESPONSE:", res.data);

      const access = res.data?.access;
      const refresh = res.data?.refresh;

      // 🚨 SAFETY CHECK (prevents broken token issues)
      if (!access || !refresh) {
        console.log("INVALID TOKEN RESPONSE:", res.data);
        alert("Login failed: Invalid token response from backend");
        return;
      }

      // 💾 STORE TOKENS
      localStorage.setItem("access", access);
      localStorage.setItem("refresh", refresh);

      console.log("ACCESS TOKEN:", access);

      alert("Login successful");

      // 🚀 NAVIGATE TO HOME
      navigate("/home");

    } catch (err) {
      console.log("LOGIN ERROR:", err.response?.data || err.message);

      alert(
        err.response?.data?.detail ||
        "Login failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.bg}>
      <div style={styles.card}>
        <h1 style={styles.title}>🌌 Travel System</h1>
        <p style={styles.subtitle}>
          Sign in to explore every part of Nepal
        </p>

        <form onSubmit={handleLogin} style={styles.form}>
          <input
            placeholder="Username"
            value={form.username}
            onChange={(e) =>
              setForm({ ...form, username: e.target.value })
            }
            style={styles.input}
          />

          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) =>
              setForm({ ...form, password: e.target.value })
            }
            style={styles.input}
          />

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p
          onClick={() => navigate("/register")}
          style={styles.link}
        >
          Don't have an account? Register
        </p>

        <p style={styles.footer}>
          Built by Travel Recommendation Engine
        </p>
      </div>
    </div>
  );
}

// 🎨 STYLES (unchanged)
const styles = {
  bg: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "radial-gradient(circle at top, #1a1a1a, #000000)",
    fontFamily: "Arial",
  },

  card: {
    width: "360px",
    padding: "35px",
    borderRadius: "14px",
    background: "rgba(20,20,20,0.85)",
    boxShadow: "0 0 25px rgba(0,255,200,0.15)",
    border: "1px solid rgba(0,255,200,0.15)",
    textAlign: "center",
    color: "#ffffff",
    backdropFilter: "blur(12px)",
  },

  title: {
    fontSize: "24px",
    marginBottom: "5px",
    color: "#00ffc3",
    textShadow: "0 0 10px rgba(0,255,195,0.5)",
  },

  subtitle: {
    fontSize: "13px",
    opacity: 0.7,
    marginBottom: "20px",
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },

  input: {
    padding: "12px",
    borderRadius: "8px",
    border: "1px solid #333",
    background: "#111",
    color: "white",
    outline: "none",
    fontSize: "14px",
  },

  button: {
    padding: "12px",
    borderRadius: "8px",
    border: "none",
    background: "linear-gradient(90deg, #00ffc3, #00a6ff)",
    color: "black",
    fontWeight: "bold",
    cursor: "pointer",
    boxShadow: "0 0 15px rgba(0,255,200,0.3)",
  },

  link: {
    marginTop: "12px",
    fontSize: "13px",
    color: "#00ffc3",
    cursor: "pointer",
  },

  footer: {
    marginTop: "15px",
    fontSize: "11px",
    opacity: 0.5,
  },
};