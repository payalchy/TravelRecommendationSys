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
          Already have an account? <span style={{ color: "#00ffc3" }}>Login</span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  bg: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "radial-gradient(circle at top, #1a1a1a, #000)",
    fontFamily: "Arial",
  },

  card: {
    width: "380px",
    padding: "35px",
    borderRadius: "16px",
    background: "rgba(20,20,20,0.9)",
    boxShadow: "0 0 30px rgba(0,255,200,0.15)",
    border: "1px solid rgba(0,255,200,0.2)",
    textAlign: "center",
    color: "white",
    backdropFilter: "blur(12px)",
  },

  title: {
    fontSize: "24px",
    color: "#00ffc3",
    marginBottom: "5px",
    textShadow: "0 0 10px rgba(0,255,195,0.4)",
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
    background: "#0f0f0f",
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
    marginTop: "15px",
    fontSize: "13px",
    color: "#aaa",
    cursor: "pointer",
  },
};