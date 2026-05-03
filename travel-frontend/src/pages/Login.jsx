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

  const isProfileComplete = (profile) => {
    return Boolean(
      profile?.budget &&
      profile?.preferred_duration &&
      profile?.preferred_travel_style?.length
    );
  };

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

      // SAFETY CHECK (prevents broken token issues)
      if (!access || !refresh) {
        console.log("INVALID TOKEN RESPONSE:", res.data);
        alert("Login failed: Invalid token response from backend");
        return;
      }

      // STORE TOKENS
      localStorage.setItem("access", access);
      localStorage.setItem("refresh", refresh);

      console.log("ACCESS TOKEN:", access);

      const profileRes = await axios.get(
        "http://127.0.0.1:8000/api/users/profile/",
        {
          headers: {
            Authorization: `Bearer ${access}`,
          },
        }
      );

      alert("Login successful");

      if (isProfileComplete(profileRes.data)) {
        navigate("/home");
      } else {
        navigate("/profile?setup=1");
      }

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
        <h1 style={styles.title}>Travel System</h1>
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

const styles = {
  bg: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "24px",
    background: "linear-gradient(135deg, #f6efe6 0%, #e8f1ff 100%)",
    fontFamily: "'Poppins', 'Segoe UI', sans-serif",
  },

  card: {
    width: "100%",
    maxWidth: "390px",
    padding: "28px",
    borderRadius: "16px",
    background: "#ffffff",
    border: "1px solid #dbe4f0",
    boxShadow: "0 10px 30px rgba(20, 40, 80, 0.10)",
    textAlign: "center",
    color: "#1f2a44",
  },

  title: {
    fontSize: "26px",
    fontWeight: "700",
    margin: "0 0 6px",
    color: "#183b66",
  },

  subtitle: {
    fontSize: "14px",
    color: "#5f6f89",
    marginBottom: "20px",
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },

  input: {
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1px solid #cdd8ea",
    background: "#f9fbff",
    color: "#1f2a44",
    outline: "none",
    fontSize: "14px",
  },

  button: {
    marginTop: "2px",
    padding: "12px",
    borderRadius: "10px",
    border: "none",
    background: "#2f6fed",
    color: "#ffffff",
    fontWeight: "600",
    cursor: "pointer",
  },

  link: {
    marginTop: "14px",
    fontSize: "13px",
    color: "#2f6fed",
    cursor: "pointer",
  },

  footer: {
    marginTop: "14px",
    fontSize: "12px",
    color: "#7a879c",
  },
};