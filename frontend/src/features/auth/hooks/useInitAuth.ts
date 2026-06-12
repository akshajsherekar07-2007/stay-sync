import { useEffect } from "react";
import { useAuthStore } from "../../../stores/authStore";
import { authService } from "../../../services/authService";
import { userService } from "../../../services/userService";

export function useInitAuth() {
  const { accessToken, setAuth, clearAuth, setToken, setInitialized } = useAuthStore();

  useEffect(() => {
    let isMounted = true;

    async function initialize() {
      try {
        if (accessToken) {
          // If we have a token, validate it by fetching current user
          try {
            const meResponse = await userService.getMe();
            if (isMounted) {
              setAuth(meResponse.data, accessToken);
            }
          } catch (err) {
            // Token might be expired. Try refreshing it.
            try {
              const refreshResponse = await authService.refresh();
              const newToken = refreshResponse.data.token.access_token;
              if (isMounted) {
                setToken(newToken);
              }
              const meResponse = await userService.getMe();
              if (isMounted) {
                setAuth(meResponse.data, newToken);
              }
            } catch (refreshErr) {
              if (isMounted) {
                clearAuth();
              }
            }
          }
        } else {
          // No access token in localStorage. Check if we can refresh via cookie.
          try {
            const refreshResponse = await authService.refresh();
            const newToken = refreshResponse.data.token.access_token;
            if (isMounted) {
              setToken(newToken);
            }
            const meResponse = await userService.getMe();
            if (isMounted) {
              setAuth(meResponse.data, newToken);
            }
          } catch (refreshErr) {
            if (isMounted) {
              clearAuth();
            }
          }
        }
      } finally {
        if (isMounted) {
          setInitialized(true);
        }
      }
    }

    initialize();

    return () => {
      isMounted = false;
    };
  }, [accessToken, setAuth, clearAuth, setToken, setInitialized]);
}
