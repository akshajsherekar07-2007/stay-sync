import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff, Lock, Mail, User, Building2 } from "lucide-react";

import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Button } from "../../../components/ui/Button";
import { registerSchema, type RegisterInput } from "../schemas/registerSchema";
import { useAuth } from "../hooks/useAuth";
import { useAuthStore } from "../../../stores/authStore";
import { cn } from "../../../lib/utils";
import { UserRole } from "../../../types/enums";
import type { RegisterRequest } from "../../../types/auth";

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
    <div className="w-full">
      <div className="mb-8 text-center md:text-left">
        <h1 className="text-3xl font-extrabold tracking-tight text-text mb-2">
          Create an account
        </h1>
        <p className="text-text-secondary text-sm">
          Join StaySync to book or list premium properties.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Role selection toggle cards */}
        <div className="space-y-2">
          <Label className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
            I am a...
          </Label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setValue("role", "student")}
              className={cn(
                "group flex flex-col items-center justify-center p-4 rounded-xl border-2 text-center transition-all duration-300 cursor-pointer shadow-sm",
                role === "student"
                  ? "border-primary bg-primary/5 text-primary scale-[0.98]"
                  : "border-border/60 bg-white text-text-secondary hover:border-primary/40 hover:shadow-md"
              )}
              disabled={isLoading}
            >
              <User className={cn("h-6 w-6 mb-2 transition-transform duration-300", role === "student" ? "scale-110" : "group-hover:scale-110")} />
              <span className="text-sm font-bold">Student</span>
            </button>
            <button
              type="button"
              onClick={() => setValue("role", "owner")}
              className={cn(
                "group flex flex-col items-center justify-center p-4 rounded-xl border-2 text-center transition-all duration-300 cursor-pointer shadow-sm",
                role === "owner"
                  ? "border-primary bg-primary/5 text-primary scale-[0.98]"
                  : "border-border/60 bg-white text-text-secondary hover:border-primary/40 hover:shadow-md"
              )}
              disabled={isLoading}
            >
              <Building2 className={cn("h-6 w-6 mb-2 transition-transform duration-300", role === "owner" ? "scale-110" : "group-hover:scale-110")} />
              <span className="text-sm font-bold">Owner</span>
            </button>
          </div>
          {errors.role && (
            <p className="text-xs text-danger font-medium animate-fade-in">
              {errors.role.message}
            </p>
          )}
        </div>

        {/* Full Name */}
        <div className="space-y-2">
          <Label htmlFor="full_name" required className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
            Full Name
          </Label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-tertiary">
              <User className="h-4 w-4" />
            </span>
            <Input
              id="full_name"
              type="text"
              placeholder="John Doe"
              className="pl-10 h-12 bg-white"
              error={!!errors.full_name}
              disabled={isLoading}
              {...registerField("full_name")}
            />
          </div>
          {errors.full_name && (
            <p className="text-xs text-danger font-medium animate-fade-in">
              {errors.full_name.message}
            </p>
          )}
        </div>

        {/* Email Address */}
        <div className="space-y-2">
          <Label htmlFor="email" required className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
            Email Address
          </Label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-tertiary">
              <Mail className="h-4 w-4" />
            </span>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              className="pl-10 h-12 bg-white"
              error={!!errors.email}
              disabled={isLoading}
              {...registerField("email")}
            />
          </div>
          {errors.email && (
            <p className="text-xs text-danger font-medium animate-fade-in">
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Passwords grid */}
        <div className="grid gap-5 sm:grid-cols-2">
          {/* Password */}
          <div className="space-y-2">
            <Label htmlFor="password" required className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
              Password
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-tertiary">
                <Lock className="h-4 w-4" />
              </span>
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="pl-10 pr-10 h-12 bg-white"
                error={!!errors.password}
                disabled={isLoading}
                {...registerField("password")}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-text-tertiary hover:text-text-secondary focus:outline-none"
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
              <p className="text-xs text-danger font-medium animate-fade-in">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword" required className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
              Confirm Password
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-tertiary">
                <Lock className="h-4 w-4" />
              </span>
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••"
                className="pl-10 pr-10 h-12 bg-white"
                error={!!errors.confirmPassword}
                disabled={isLoading}
                {...registerField("confirmPassword")}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-text-tertiary hover:text-text-secondary focus:outline-none"
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
              <p className="text-xs text-danger font-medium animate-fade-in">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>
        </div>

        <Button type="submit" className="w-full h-12 text-base mt-4" loading={isLoading}>
          Create Account
        </Button>
      </form>

      <div className="mt-8 text-center text-sm text-text-secondary">
        <p>
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-primary hover:text-primary-dark hover:underline transition-colors"
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
