import "./styles/app.css";
import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
// const API = "http://127.0.0.1:8000";

const API = import.meta.env.VITE_API_URL || "";

export default function App() {
  const [page, setPage] = useState("login");
  const [loginMode, setLoginMode] = useState("user");
  const [verifyStep, setVerifyStep] = useState("email");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [email, setEmail] = useState("");
  const [mobile, setMobile] = useState("");
  const [verificationToken, setVerificationToken] = useState("");

  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("");

  const [status, setStatus] = useState("");
  const [risk, setRisk] = useState(null);

  const [alerts, setAlerts] = useState([]);
  const [reports, setReports] = useState([]);

  useEffect(() => {
    setUsername("");
    setPassword("");
    setEmail("");
    setMobile("");
    setVerificationToken("");
    setOtp("");
    setNewPassword("");
    setStatus("");
  }, [page]);

  const login = async () => {
    if (!username || !password) {
      setStatus("⚠ Username and Password are required");
      return;
    }
    try {
      const res = await axios.post(`${API}/login`, { username, password });

      if (loginMode === "admin" && res.data.role !== "admin") {
        setStatus("❌ Not authorized as admin");
        return;
      }

      const { access_token, user_id, role } = res.data;
      localStorage.setItem("token", access_token);
      setUserId(user_id);
      setRole(role);
      setRisk(null);
      setPage("dashboard");
    } catch (err) {
      const msg = err.response?.data?.detail || "";
      if (err.response?.status === 403) {
        setVerifyStep("token");
        setStatus(`🚨 ${msg || "Account requires verification."}`);
        setPage("verify");
      } else {
        setStatus("❌ Invalid Credentials");
      }
    }
  };

  const register = async () => {
    if (!username || !password || !email || !mobile) {
      setStatus("⚠ All fields marked * are required");
      return;
    }
    try {
      await axios.post(`${API}/register`, { username, password, email, mobile });
      setStatus("✅ OTP Sent to your Email. Please verify to activate account.");
      setVerifyStep("token");
      setPage("verify");
    } catch (err) {
      const msg = err.response?.data?.detail || "Registration failed. Please try again.";
      setStatus(`❌ ${msg}`);
    }
  };

  const sendOtp = async () => {
    if (!username || !email) {
      setStatus("⚠ Username and Email are required");
      return;
    }
    try {
      await axios.post(`${API}/forgot-password`, { email });
      setStatus("✅ OTP Sent to Email");
      setPage("reset");
    } catch {
      setStatus("❌ Email not found");
    }
  };

  const resetPassword = async () => {
    if (!email || !otp || !newPassword) {
      setStatus("⚠ All fields marked * are required");
      return;
    }
    try {
      await axios.post(`${API}/reset-password`, {
        email,
        otp,
        new_password: newPassword,
      });
      setStatus("✅ Password Reset Successful. Redirecting...");
      setTimeout(() => setPage("login"), 1500);
    } catch {
      setStatus("❌ Invalid OTP");
    }
  };

  const verifyUser = async () => {
    if (!verificationToken) {
      setStatus("⚠ Verification Token is required");
      return;
    }
    try {
      const res = await axios.post(`${API}/verify-user`, { token: verificationToken });
      const { access_token, user_id, role } = res.data;
      localStorage.setItem("token", access_token);
      setUserId(user_id);
      setRole(role);
      
      setStatus("✅ Account Verified Successfully. Redirecting...");
      setTimeout(() => {
        setVerifyStep("email");
        setPage("dashboard");
      }, 1500);
    } catch (err) {
      const msg = err.response?.data?.detail || "Invalid or expired OTP.";
      setStatus(`❌ ${msg}`);
    }
  };

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
  });

  const logNormal = async () => {
    try {
      await axios.post(`${API}/log-behavior`, {
        user_id: userId,
        location: "Hyderabad",
        device: "Chrome_Windows",
        access_speed: 1.2,
      }, getAuthHeaders());
      setStatus("🟢 Normal Behavior Logged");
    } catch {
      setStatus("❌ Session Expired. Please Login Again.");
      setPage("login");
    }
  };

  const logAbnormal = async () => {
    try {
      await axios.post(`${API}/log-behavior`, {
        user_id: userId,
        location: "Unknown",
        device: "Suspicious_Device",
        access_speed: 15,
      }, getAuthHeaders());
      setStatus("🔴 Abnormal Behavior Logged");
    } catch {
      setStatus("❌ Session Expired");
      setPage("login");
    }
  };

  const analyzeRisk = async () => {
    try {
      const res = await axios.post(`${API}/analyze-risk/${userId}`, {}, getAuthHeaders());
      setRisk(res.data);

      if (res.data.risk_level === "High") {
        setVerifyStep("email");
        setStatus("🚨 HIGH RISK DETECTED – ACCOUNT BLOCKED");
        setPage("verify");
      }
    } catch {
      setPage("login");
    }
  };

  const loadAlerts = async () => {
    try {
      const res = await axios.get(`${API}/admin/notifications`, getAuthHeaders());
      setAlerts(res.data);
    } catch {
      setPage("login");
    }
  };

  const loadReports = async () => {
    try {
      const res = await axios.get(`${API}/admin/risk-reports`, getAuthHeaders());
      setReports(res.data);
    } catch {
      setPage("login");
    }
  };

  const unblockUser = async (blockedUsername) => {
    try {
      await axios.post(`${API}/admin/unblock/${blockedUsername}`, {}, getAuthHeaders());
      setStatus("✅ User Unblocked");
      loadAlerts();
      loadReports();
    } catch {
      setStatus("❌ Action Failed");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUserId("");
    setRole("");
    setPage("login");
  };

  useEffect(() => {
    if (role === "admin") {
      loadAlerts();
      loadReports();
    }
  }, [role]);

  /* ================= PAGES ================= */

  if (page === "login") {
    return (
      <div className="page login-bg">
        <div className="card">
          <h2>🛡 Zero Trust Security</h2>

          <div>
            <button onClick={() => setLoginMode("user")}>User Login</button>
            <button onClick={() => setLoginMode("admin")}>Admin Login</button>
          </div>

          <input placeholder="Username *" value={username} onChange={(e) => setUsername(e.target.value)} />

          <div className="password-box">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password *"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? "🙈" : "👁️"}
            </span>
          </div>

          <button className="primary" onClick={login}>Login</button>

          {loginMode === "user" && (
            <>
              <p className="link" onClick={() => setPage("register")}>Register</p>
              <p className="link" onClick={() => setPage("forgot")}>Forgot Password?</p>
            </>
          )}

          <p className="status">{status}</p>
        </div>
      </div>
    );
  }

  if (page === "register") {
    return (
      <div className="page register-bg">
        <div className="card">
          <h2>Create Account</h2>
          <input placeholder="Username *" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input placeholder="Email *" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="Mobile *" value={mobile} onChange={(e) => setMobile(e.target.value)} />
          <input type="password" placeholder="Password *" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="primary" onClick={register}>Register</button>
          <button className="backBtn" onClick={() => setPage("login")}>← Back</button>
          <p className="status">{status}</p>
        </div>
      </div>
    );
  }

  if (page === "forgot") {
    return (
      <div className="page forgot-bg">
        <div className="card">
          <h2>Forgot Password</h2>
          <input placeholder="Username *" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input placeholder="Registered Email *" value={email} onChange={(e) => setEmail(e.target.value)} />
          <button className="primary" onClick={sendOtp}>Send OTP</button>
          <button className="backBtn" onClick={() => setPage("login")}>← Back</button>
          <p className="status">{status}</p>
        </div>
      </div>
    );
  }

  if (page === "reset") {
    return (
      <div className="page reset-bg">
        <div className="card">
          <h2>Reset Password</h2>
          <input placeholder="Email *" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="OTP *" value={otp} onChange={(e) => setOtp(e.target.value)} />
          <input type="password" placeholder="New Password *" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          <button className="primary" onClick={resetPassword}>Reset</button>
          <button className="backBtn" onClick={() => setPage("login")}>← Back</button>
          <p className="status">{status}</p>
        </div>
      </div>
    );
  }

  if (page === "verify") {
    return (
      <div className="page verify-bg">
        <div className="card alert-card-big">
          {verifyStep === "token" && status.includes("OTP Sent") ? (
            <>
              <h2>Verify Your Account</h2>
              <p>Please enter the 6-digit OTP sent to your email.</p>
            </>
          ) : (
            <>
              <h1 className="blink">🚨 SECURITY THREAT</h1>
              <h3>ACCOUNT BLOCKED</h3>
            </>
          )}

          {verifyStep === "email" && (
            <>
              <input placeholder="Registered Email *" value={email} onChange={(e) => setEmail(e.target.value)} />
              <button className="primary" onClick={() => setVerifyStep("token")}>Continue</button>
            </>
          )}

          {verifyStep === "token" && (
            <>
              <input placeholder="Verification Token *" value={verificationToken} onChange={(e) => setVerificationToken(e.target.value)} />
              <button className="primary" onClick={verifyUser}>Verify</button>
            </>
          )}

          <button className="backBtn" onClick={() => { setVerifyStep("email"); setPage("login"); }}>
            ← Back to Login
          </button>

          <p className="status">{status}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`dashboard ${role === "admin" ? "admin-bg" : "user-bg"}`}>
      <button className="logoutBtn" onClick={logout}>← Logout</button>
      <h2>{role === "admin" ? "Admin Security Operations Center Dashboard" : "User Cyber Control Panel"}</h2>

      {role === "user" && (
        <div className="user-panel">
          <div className="action normal" onClick={logNormal}>🟢 Log Normal Behavior</div>
          <div className="action abnormal" onClick={logAbnormal}>🔴 Log Abnormal Behavior</div>
          <div className="action analyze" onClick={analyzeRisk}>⚠ Analyze Risk</div>

          {risk && (
            <div className={`risk-box-big ${risk.risk_level.toLowerCase()}`}>
              <h1>{risk.risk_level} Risk</h1>
              <h3>Action: {risk.action}</h3>
            </div>
          )}
        </div>
      )}

      {role === "admin" && (
        <div className="admin-panel">
          <h3>🚨 Alerts</h3>

          {alerts.map((a, i) => (
            <div key={i} className="alert-row">
              <div>
                <b>User:</b> {a.username}<br />
                <b>Alert:</b> {a.message}<br />
                <b>Time:</b>{" "}
                {new Date(a.timestamp).toLocaleString("en-IN", {
                  timeZone: "Asia/Kolkata",
                  day: "2-digit",
                  month: "2-digit",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}

              </div>
              <button onClick={() => unblockUser(a.username)}>Unblock</button>
            </div>
          ))}

          <h3>📊 Risk Analytics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={reports.slice().reverse()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis hide />
              <YAxis />
              <Tooltip />
              <Line dataKey="risk_score" stroke="red" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="status">{status}</p>
    </div>
  );
}
