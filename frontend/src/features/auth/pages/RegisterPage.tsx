import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff, Lock, Mail, User, Building2 } from "lucide-react";

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
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
      // Strip confirmPassword before sending to api
      const { confirmPassword, ...registerData } = data;
      // Map string roles to UserRole enum values
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
    <Card className="w-full border-border bg-card shadow-lg animate-slide-up">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold tracking-tight text-center md:text-left">
          Create an account
        </CardTitle>
        <CardDescription className="text-center md:text-left">
          Join StaySync today as a student or property owner.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Role selection toggle cards */}
          <div className="space-y-2">
            <Label>I am a...</Label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setValue("role", "student")}
                className={cn(
                  "flex flex-col items-center justify-center p-3 rounded-lg border-2 text-center transition-all duration-200 cursor-pointer",
                  role === "student"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border bg-card text-text-secondary hover:border-border-hover"
                )}
                disabled={isLoading}
              >
                <User className="h-5 w-5 mb-1.5" />
                <span className="text-sm font-semibold">Student</span>
                <span className="text-[10px] text-text-tertiary">Looking for stays</span>
              </button>
              <button
                type="button"
                onClick={() => setValue("role", "owner")}
                className={cn(
                  "flex flex-col items-center justify-center p-3 rounded-lg border-2 text-center transition-all duration-200 cursor-pointer",
                  role === "owner"
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border bg-card text-text-secondary hover:border-border-hover"
                )}
                disabled={isLoading}
              >
                <Building2 className="h-5 w-5 mb-1.5" />
                <span className="text-sm font-semibold">Owner</span>
                <span className="text-[10px] text-text-tertiary">List properties</span>
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
            <Label htmlFor="full_name" required>
              Full Name
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary">
                <User className="h-4 w-4" />
              </span>
              <Input
                id="full_name"
                type="text"
                placeholder="John Doe"
                className="pl-10 animate-fade-in"
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
            <Label htmlFor="email" required>
              Email Address
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary">
                <Mail className="h-4 w-4" />
              </span>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                className="pl-10 animate-fade-in"
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

          {/* Password */}
          <div className="space-y-2">
            <Label htmlFor="password" required>
              Password
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary">
                <Lock className="h-4 w-4" />
              </span>
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="pl-10 pr-10 animate-fade-in"
                error={!!errors.password}
                disabled={isLoading}
                {...registerField("password")}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-tertiary hover:text-text-secondary focus:outline-none"
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
            <Label htmlFor="confirmPassword" required>
              Confirm Password
            </Label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary">
                <Lock className="h-4 w-4" />
              </span>
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••"
                className="pl-10 pr-10 animate-fade-in"
                error={!!errors.confirmPassword}
                disabled={isLoading}
                {...registerField("confirmPassword")}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-tertiary hover:text-text-secondary focus:outline-none"
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

          <Button type="submit" className="w-full mt-2" loading={isLoading}>
            Sign Up
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex flex-col space-y-2 text-center text-sm text-text-secondary">
        <div className="w-full border-t border-border my-2" />
        <p>
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-primary hover:text-primary-dark hover:underline transition-colors"
          >
            Sign In
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
