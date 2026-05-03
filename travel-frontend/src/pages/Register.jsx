import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(
        "http://127.0.0.1:8000/api/users/register/",
        {
          username: form.username,
          email: form.email,
          password: form.password,
        }
      );

      alert("Registered successfully 🚀");
      navigate("/");

    } catch (err) {
      console.log(err);
      alert("Registration failed ❌");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.bg}>
      <div style={styles.card}>
        <h1 style={styles.title}>🌍 Create Account</h1>
        <p style={styles.subtitle}>
          Join TravelAI and explore smarter travel
        </p>

        <form onSubmit={handleRegister} style={styles.form}>
          
          <input
            placeholder="Username"
            value={form.username}
            onChange={(e) =>
              setForm({ ...form, username: e.target.value })
            }
            style={styles.input}
          />

          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) =>
              setForm({ ...form, email: e.target.value })
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

          <button
            type="submit"
            disabled={loading}
            style={styles.button}
          >
            {loading ? "Creating account..." : "Register 🚀"}
          </button>
        </form>

        <p
          onClick={() => navigate("/")}
          style={styles.link}
        >
          Already have an account? <span style={{ color: "#2f6fed" }}>Login</span>
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
    maxWidth: "400px",
    padding: "28px",
    borderRadius: "16px",
    background: "#ffffff",
    boxShadow: "0 10px 30px rgba(20, 40, 80, 0.10)",
    border: "1px solid #dbe4f0",
    textAlign: "center",
    color: "#1f2a44",
  },

  title: {
    fontSize: "26px",
    color: "#183b66",
    margin: "0 0 6px",
    fontWeight: "700",
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
    color: "#5f6f89",
    cursor: "pointer",
  },
};