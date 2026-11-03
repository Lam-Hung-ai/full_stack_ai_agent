import { Suspense } from "react";
import { VerifyEmailScreen } from "@/features/auth";

export default function VerifyEmailPage() {
  // useSearchParams (the ?token= from the letter) needs a Suspense boundary.
  return (
    <Suspense>
      <VerifyEmailScreen />
    </Suspense>
  );
}
