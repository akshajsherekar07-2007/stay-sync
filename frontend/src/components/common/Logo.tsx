import { Link } from "react-router-dom";
import { Building2 } from "lucide-react";
import styles from "./Logo.module.css";

interface LogoProps {
  className?: string;
  onClick?: () => void;
  collapsed?: boolean;
}

export function Logo({ className = "", onClick, collapsed = false }: LogoProps) {
  return (
    <Link to="/" className={`${styles.logo} ${className}`} onClick={onClick}>
      <div className={styles.iconWrapper}>
        <Building2 className={styles.icon} aria-hidden="true" />
      </div>
      {!collapsed && (
        <span className={styles.text}>
          <span className={styles.textDark}>Stay</span>
          <span className={styles.textPrimary}>Sync</span>
        </span>
      )}
    </Link>
  );
}
