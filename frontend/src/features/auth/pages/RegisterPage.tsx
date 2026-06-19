import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff, Lock, Mail, User, Building2, Phone, Hash, Shield, PhoneCall, GraduationCap, Calendar, Briefcase } from "lucide-react";

import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Button } from "../../../components/ui/Button";
import { registerSchema, type RegisterInput } from "../schemas/registerSchema";
import { useAuth } from "../hooks/useAuth";
import { useAuthStore } from "../../../stores/authStore";
import { cn } from "../../../lib/utils";
import { UserRole } from "../../../types/enums";
import type { RegisterRequest } from "../../../types/auth";
import styles from "./RegisterPage.module.css";

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();

  const {
    register: registerField,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirmPassword: "",
      role: "student",
    },
  });

  const role = watch("role");

  const onSubmit = async (data: RegisterInput) => {
    try {
      const { confirmPassword, ...registerData } = data;
      const payload: RegisterRequest = {
        email: registerData.email,
        password: registerData.password,
        role: registerData.role === "owner" ? UserRole.OWNER : UserRole.STUDENT,
        full_name: registerData.full_name,
      };
      
      await register(payload);
      toast.success("Account created successfully! Welcome to StaySync.");
      
      const currentUser = useAuthStore.getState().user;
      if (currentUser?.role === "owner") {
        navigate("/owner/dashboard", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: any) {
      toast.error(
        err.response?.data?.error?.message || 
        "Registration failed. Please check your details and try again."
      );
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          Create an account
        </h1>
        <p className={styles.subtitle}>
          Join StaySync to book or list premium properties.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        {/* Role selection toggle cards */}
        <div className={styles.formGroup}>
          <Label className={styles.label}>
            I am a...
          </Label>
          <div className={styles.roleGrid}>
            <button
              type="button"
              onClick={() => setValue("role", "student")}
              className={cn(styles.roleCard, role === "student" && styles.roleCardActive)}
              disabled={isLoading}
            >
              <User className={styles.roleIcon} />
              <span className={styles.roleText}>Student</span>
            </button>
            <button
              type="button"
              onClick={() => setValue("role", "owner")}
              className={cn(styles.roleCard, role === "owner" && styles.roleCardActive)}
              disabled={isLoading}
            >
              <Building2 className={styles.roleIcon} />
              <span className={styles.roleText}>Owner</span>
            </button>
          </div>
          {errors.role && (
            <p className={styles.errorMessage}>
              {errors.role.message}
            </p>
          )}
        </div>

        {/* Section: Personal Details */}
        <div className={styles.section}>
          <h3 className={styles.sectionHeader}>Personal Details</h3>
          <div className={styles.passwordGrid}>
            <div className={styles.formGroup}>
              <Label htmlFor="full_name" required className={styles.label}>
                Full Name
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <User className="h-4 w-4" />
                </span>
                <Input
                  id="full_name"
                  type="text"
                  placeholder="John Doe"
                  className={styles.inputWithIconLeft}
                  error={!!errors.full_name}
                  disabled={isLoading}
                  {...registerField("full_name")}
                />
              </div>
              {errors.full_name && (
                <p className={styles.errorMessage}>{errors.full_name.message}</p>
              )}
            </div>

            <div className={styles.formGroup}>
              <Label htmlFor="phone" className={styles.label}>
                Phone Number <span className={styles.optionalText}>(optional)</span>
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Phone className="h-4 w-4" />
                </span>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+91 98765 43210"
                  className={styles.inputWithIconLeft}
                  disabled={isLoading}
                  {...registerField("phone")}
                />
              </div>
            </div>

            <div className={styles.formGroup}>
              <Label htmlFor="age" className={styles.label}>
                Age <span className={styles.optionalText}>(optional)</span>
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Hash className="h-4 w-4" />
                </span>
                <Input
                  id="age"
                  type="number"
                  placeholder="e.g. 21"
                  className={styles.inputWithIconLeft}
                  disabled={isLoading}
                  {...registerField("age")}
                />
              </div>
            </div>

            <div className={styles.formGroup}>
              <Label htmlFor="aadhar" className={styles.label}>
                Aadhar Number <span className={styles.optionalText}>(optional)</span>
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Shield className="h-4 w-4" />
                </span>
                <Input
                  id="aadhar"
                  type="text"
                  placeholder="XXXX XXXX XXXX"
                  className={styles.inputWithIconLeft}
                  disabled={isLoading}
                  {...registerField("aadhar")}
                />
              </div>
            </div>

            {role === "student" && (
              <div className={cn(styles.formGroup, styles.colSpan2)}>
                <Label htmlFor="emergencyContact" className={styles.label}>
                  Emergency Contact <span className={styles.optionalText}>(optional)</span>
                </Label>
                <div className={styles.inputWrapper}>
                  <span className={styles.inputIconLeft}>
                    <PhoneCall className="h-4 w-4" />
                  </span>
                  <Input
                    id="emergencyContact"
                    type="tel"
                    placeholder="+91 98765 43210 (Parent/Guardian)"
                    className={styles.inputWithIconLeft}
                    disabled={isLoading}
                    {...registerField("emergencyContact")}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section: Role Specific */}
        <div className={styles.section}>
          <h3 className={styles.sectionHeader}>
            {role === "student" ? "College Details" : "Business Details"}
          </h3>
          <div className={styles.passwordGrid}>
            {role === "student" && (
              <>
                <div className={styles.formGroup}>
                  <Label htmlFor="collegeName" className={styles.label}>
                    College Name <span className={styles.optionalText}>(optional)</span>
                  </Label>
                  <div className={styles.inputWrapper}>
                    <span className={styles.inputIconLeft}>
                      <GraduationCap className="h-4 w-4" />
                    </span>
                    <Input
                      id="collegeName"
                      type="text"
                      placeholder="e.g. IIT Bombay"
                      className={styles.inputWithIconLeft}
                      disabled={isLoading}
                      {...registerField("collegeName")}
                    />
                  </div>
                </div>
                <div className={styles.formGroup}>
                  <Label htmlFor="collegeYear" className={styles.label}>
                    College Year <span className={styles.optionalText}>(optional)</span>
                  </Label>
                  <div className={styles.inputWrapper}>
                    <span className={styles.inputIconLeft}>
                      <Calendar className="h-4 w-4" />
                    </span>
                    <Input
                      id="collegeYear"
                      type="text"
                      placeholder="e.g. 2nd Year"
                      className={styles.inputWithIconLeft}
                      disabled={isLoading}
                      {...registerField("collegeYear")}
                    />
                  </div>
                </div>
              </>
            )}

            {role === "owner" && (
              <>
                <div className={cn(styles.formGroup, styles.colSpan2)}>
                  <Label htmlFor="businessName" className={styles.label}>
                    Business / Agency Name <span className={styles.optionalText}>(optional)</span>
                  </Label>
                  <div className={styles.inputWrapper}>
                    <span className={styles.inputIconLeft}>
                      <Briefcase className="h-4 w-4" />
                    </span>
                    <Input
                      id="businessName"
                      type="text"
                      placeholder="e.g. StaySync PG Accommodations"
                      className={styles.inputWithIconLeft}
                      disabled={isLoading}
                      {...registerField("businessName")}
                    />
                  </div>
                </div>

                <div className={cn(styles.formGroup, styles.colSpan2)}>
                  <Label htmlFor="officeNumber" className={styles.label}>
                    Office Number <span className={styles.optionalText}>(optional)</span>
                  </Label>
                  <div className={styles.inputWrapper}>
                    <span className={styles.inputIconLeft}>
                      <PhoneCall className="h-4 w-4" />
                    </span>
                    <Input
                      id="officeNumber"
                      type="tel"
                      placeholder="+91 98765 43210"
                      className={styles.inputWithIconLeft}
                      disabled={isLoading}
                      {...registerField("officeNumber")}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Section: Account Security */}
        <div className={styles.section}>
          <h3 className={styles.sectionHeader}>Account Security</h3>
          <div className={styles.passwordGrid}>
            <div className={cn(styles.formGroup, styles.colSpan2)}>
              <Label htmlFor="email" required className={styles.label}>
                Email Address
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Mail className="h-4 w-4" />
                </span>
                <Input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  className={styles.inputWithIconLeft}
                  error={!!errors.email}
                  disabled={isLoading}
                  {...registerField("email")}
                />
              </div>
              {errors.email && (
                <p className={styles.errorMessage}>{errors.email.message}</p>
              )}
            </div>

            <div className={styles.formGroup}>
              <Label htmlFor="password" required className={styles.label}>
                Password
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Lock className="h-4 w-4" />
                </span>
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className={cn(styles.inputWithIconLeft, styles.inputWithIconRight)}
                  error={!!errors.password}
                  disabled={isLoading}
                  {...registerField("password")}
                />
                <button
                  type="button"
                  className={styles.inputIconRight}
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className={styles.errorMessage}>{errors.password.message}</p>
              )}
            </div>

            <div className={styles.formGroup}>
              <Label htmlFor="confirmPassword" required className={styles.label}>
                Confirm Password
              </Label>
              <div className={styles.inputWrapper}>
                <span className={styles.inputIconLeft}>
                  <Lock className="h-4 w-4" />
                </span>
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className={cn(styles.inputWithIconLeft, styles.inputWithIconRight)}
                  error={!!errors.confirmPassword}
                  disabled={isLoading}
                  {...registerField("confirmPassword")}
                />
                <button
                  type="button"
                  className={styles.inputIconRight}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={isLoading}
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className={styles.errorMessage}>{errors.confirmPassword.message}</p>
              )}
            </div>
          </div>
        </div>

        <Button type="submit" className={styles.submitBtn} loading={isLoading}>
          Create Account
        </Button>
      </form>

      <div className={styles.footer}>
        <p>
          Already have an account?{" "}
          <Link
            to="/login"
            className={styles.signInLink}
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
