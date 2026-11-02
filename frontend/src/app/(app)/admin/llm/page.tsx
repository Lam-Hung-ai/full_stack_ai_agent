import { PageHeader } from "@/components/layout/page-header";
import { LlmAdminScreen } from "@/features/admin";

export const instant = false;

export default function LlmAdminPage() {
  return (
    <>
      <PageHeader />
      <div className="min-h-0 flex-1">
        <LlmAdminScreen />
      </div>
    </>
  );
}
