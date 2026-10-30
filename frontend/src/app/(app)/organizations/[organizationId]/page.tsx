import { OrganizationScreen } from "@/features/organizations";

export const instant = false;

export default async function OrganizationPage({
  params,
}: PageProps<"/organizations/[organizationId]">) {
  const { organizationId } = await params;
  return <OrganizationScreen organizationId={organizationId} />;
}
