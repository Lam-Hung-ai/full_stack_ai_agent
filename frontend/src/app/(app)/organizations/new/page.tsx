import { CreateOrganizationScreen } from "@/features/organizations";

// Client-only screen: nothing static to validate for instant navigation.
export const instant = false;

export default function NewOrganizationPage() {
  return <CreateOrganizationScreen />;
}
