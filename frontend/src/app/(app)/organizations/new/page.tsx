import { PageHeader } from "@/components/layout/page-header";
import { CreateOrganizationScreen } from "@/features/organizations";

// Client-only screen: nothing static to validate for instant navigation.
export const instant = false;

export default function NewOrganizationPage() {
  return (
    <>
      <PageHeader />
      <div className="min-h-0 flex-1">
        <CreateOrganizationScreen />
      </div>
    </>
  );
}
