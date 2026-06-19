import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";

import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Button } from "../../../components/ui/Button";
import { loginSchema, type LoginInput } from "../schemas/loginSchema";
import { useAuth } from "../hooks/useAuth";
import { useAuthStore } from "../../../stores/authStore";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const {
    register: registerField,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginInput) => {
    try {
      await login(data);
      toast.success("Welcome back to StaySync!");
      
      const currentUser = useAuthStore.getState().user;
      const from = (location.state as any)?.from?.pathname;
      
      if (from) {
        navigate(from, { replace: true });
      } else if (currentUser?.role === "owner") {
        navigate("/owner/dashboard", { replace: true });
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (err: any) {
      toast.error(
        err.response?.data?.error?.message || 
        "Login failed. Please check your credentials and try again."
      );
    }
  };

  const handleQuickLogin = (email: string) => {
    setValue("email", email);
    setValue("password", "Password123");
  };

  return (
    <div className="w-full">
      <div className="mb-8 text-center md:text-left">
        <h1 className="text-3xl font-extrabold tracking-tight text-text mb-2">
          Welcome back
        </h1>
        <p className="text-text-secondary text-sm">
          Enter your credentials to access your account.
        </p>
      </div>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
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

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" required className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
              Password
            </Label>
            <Link to="#" className="text-xs font-semibold text-primary hover:text-primary-dark hover:underline">
              Forgot password?
            </Link>
          </div>
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

        <Button type="submit" className="w-full h-12 text-base mt-2" loading={isLoading}>
          Sign In
        </Button>
      </form>

      <div className="mt-8 text-center text-sm text-text-secondary">
        <p>
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-primary hover:text-primary-dark hover:underline transition-colors"
          >
            Create an account
          </Link>
        </p>
      </div>

      {/* Dev Quick Login Panel */}
      <div className="mt-10 rounded-xl bg-bg-secondary p-5 border border-border/60">
        <p className="text-[11px] uppercase tracking-wider font-bold text-text-tertiary mb-3">
          Developer Quick Access
        </p>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => handleQuickLogin("student@example.com")}
            className="group flex flex-col items-start p-3 text-left rounded-lg border border-border/60 bg-white hover:border-primary/30 hover:shadow-sm transition-all cursor-pointer"
            disabled={isLoading}
          >
            <span className="text-sm font-bold text-text group-hover:text-primary transition-colors">Student Demo</span>
            <span className="text-xs text-text-secondary truncate w-full mt-0.5">
              student@example.com
            </span>
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin("owner@example.com")}
            className="group flex flex-col items-start p-3 text-left rounded-lg border border-border/60 bg-white hover:border-primary/30 hover:shadow-sm transition-all cursor-pointer"
            disabled={isLoading}
          >
            <span className="text-sm font-bold text-text group-hover:text-primary transition-colors">Owner Demo</span>
            <span className="text-xs text-text-secondary truncate w-full mt-0.5">
              owner@example.com
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
