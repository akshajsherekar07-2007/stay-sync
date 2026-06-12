import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import { queryClient } from "../lib/queryClient";
import { AppRouter } from "./router";
import { useInitAuth } from "../features/auth/hooks/useInitAuth";
import { Toaster } from "../components/common/Toaster";

function AppContent() {
  // Run app boot authentication check
  useInitAuth();

  return (
    <BrowserRouter>
      <AppRouter />
      <Toaster />
    </BrowserRouter>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
