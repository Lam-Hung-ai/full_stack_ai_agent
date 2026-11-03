import { Suspense } from "react";
import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  // useSearchParams (the ?next= target) needs a Suspense boundary.
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
