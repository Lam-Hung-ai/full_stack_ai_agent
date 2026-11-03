import { PageHeader } from "@/components/layout/page-header";
import { OrganizationScreen } from "@/features/organizations";

export const instant = false;

export default async function OrganizationPage({
  params,
}: PageProps<"/organizations/[organizationId]">) {
  const { organizationId } = await params;
  return (
    <>
      <PageHeader />
      <div className="min-h-0 flex-1">
        <OrganizationScreen organizationId={organizationId} />
      </div>
    </>
  );
}
