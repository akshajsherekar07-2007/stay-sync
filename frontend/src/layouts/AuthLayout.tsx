import { Link, Navigate, Outlet } from "react-router-dom";
import { Building2 } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { Logo } from "../components/common/Logo";
import styles from "./AuthLayout.module.css";

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className={styles.container}>
      {/* Decorative Left Panel (Desktop only) */}
      <div className={styles.leftPanel}>
        {/* Subtle Background Pattern */}
        <div className={styles.bgPattern} />
        
        {/* Soft glowing orb in the background */}
        <div className={styles.glowOrb1} />
        <div className={styles.glowOrb2} />

        <div className={styles.brand}>
          <Logo className={styles.logoLight} />
        </div>

        {/* Abstract Product Mockup */}
        <div className={styles.mockupWrapper}>
          <div className={styles.mockupCard}>
            <div className={styles.mockupHeader}>
              <div className={styles.mockupDots}>
                <div className={styles.mockupDot} />
                <div className={styles.mockupDot} />
                <div className={styles.mockupDot} />
              </div>
            </div>
            <div className={styles.mockupContent}>
              <div className={styles.mockupTitle} />
              <div className={styles.mockupLines}>
                <div className={styles.mockupLine1} />
                <div className={styles.mockupLine2} />
                <div className={styles.mockupLine3} />
              </div>
              <div className={styles.mockupBoxes}>
                <div className={styles.mockupBox1} />
                <div className={styles.mockupBox2} />
              </div>
            </div>
          </div>
        </div>

        <div className={styles.testimonial}>
          <blockquote className={styles.quote}>
            "StaySync has completely transformed how we manage our properties. 
            The waitlist features and instant holds fill our beds 40% faster than before."
          </blockquote>
          <div className={styles.author}>
            <div className={styles.authorAvatar}>
              S
            </div>
            <div>
              <p className={styles.authorName}>Sarah Jenkins</p>
              <p className={styles.authorTitle}>Property Manager at Apex Housing</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel (Form content) */}
      <div className={styles.rightPanel}>
        <div className={styles.formWrapper}>
          {/* Mobile Branding */}
          <div className={styles.mobileBrand}>
            <Logo />
          </div>
          {/* Routed components (Login / Register form) */}
          <Outlet />
        </div>
      </div>
    </div>
  );
}
