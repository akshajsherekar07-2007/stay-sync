import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
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
    <Card className="w-full border-border bg-card shadow-lg animate-slide-up">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold tracking-tight text-center md:text-left">
          Sign in
        </CardTitle>
        <CardDescription className="text-center md:text-left">
          Enter your email and credentials to access your portal.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
                placeholder="student@example.com"
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

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" required>
                Password
              </Label>
            </div>
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

          <Button type="submit" className="w-full mt-2" loading={isLoading}>
            Sign In
          </Button>
        </form>

        {/* Dev Quick Login Panel */}
        <div className="mt-6 rounded-lg bg-bg-secondary p-4 border border-border">
          <p className="text-xs font-semibold text-text-secondary mb-2">
            Developer Quick Fill:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("student@example.com")}
              className="flex flex-col items-start p-2 text-left rounded-md border border-border bg-card hover:bg-bg-tertiary hover:border-border-hover transition-colors cursor-pointer"
              disabled={isLoading}
            >
              <span className="text-xs font-semibold text-primary">Student</span>
              <span className="text-[10px] text-text-secondary truncate w-full">
                student@example.com
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("owner@example.com")}
              className="flex flex-col items-start p-2 text-left rounded-md border border-border bg-card hover:bg-bg-tertiary hover:border-border-hover transition-colors cursor-pointer"
              disabled={isLoading}
            >
              <span className="text-xs font-semibold text-primary">Owner</span>
              <span className="text-[10px] text-text-secondary truncate w-full">
                owner@example.com
              </span>
            </button>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col space-y-2 text-center text-sm text-text-secondary">
        <div className="w-full border-t border-border my-2" />
        <p>
          Don&apos;t have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-primary hover:text-primary-dark hover:underline transition-colors"
          >
            Create an account
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
