import { Suspense } from "react";
import { ResetPasswordForm } from "@/features/auth";

export default function ResetPasswordPage() {
  // useSearchParams (the ?token= from the letter) needs a Suspense boundary.
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
