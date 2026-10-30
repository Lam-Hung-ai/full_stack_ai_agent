import { Suspense } from "react";
import { InvitationScreen } from "@/features/organizations";

export default function InvitationPage() {
  // useSearchParams (the ?token= from the letter) needs a Suspense boundary.
  return (
    <Suspense>
      <InvitationScreen />
    </Suspense>
  );
}
