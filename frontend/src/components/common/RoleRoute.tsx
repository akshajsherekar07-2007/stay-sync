import { Navigate, Outlet, Link } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { UserRole } from "../../types/enums";
import { LoadingSpinner } from "./LoadingSpinner";
import { Button } from "../ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../ui/Card";

interface RoleRouteProps {
  allowedRoles: (UserRole | string)[];
}

export function RoleRoute({ allowedRoles }: RoleRouteProps) {
  const { user, isAuthenticated, isInitialized } = useAuthStore();

  if (!isInitialized) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-bg">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <div className="flex min-h-[500px] w-full items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg border-danger/20">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger" aria-hidden="true">
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 15v2m0-8v6m0 5h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <CardTitle className="text-xl">Access Denied</CardTitle>
            <CardDescription>
              You do not have permission to access this resource.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center text-sm text-text-secondary">
            This area is restricted to {allowedRoles.join(" or ")} accounts only. Your account role is "{user.role}".
          </CardContent>
          <CardFooter className="justify-center">
            <Button asChild variant="default">
              <Link to="/dashboard">Go to Dashboard</Link>
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return <Outlet />;
}
