"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSession } from "@/features/auth";
import { AssignmentsPanel } from "./assignments-panel";
import { ConnectionsPanel } from "./connections-panel";
import { ModelsPanel } from "./models-panel";

/** System administration of the models agents run on (QD-34). Superusers
 * only: the page hides itself for others and the API refuses every call. */
export function LlmAdminScreen() {
  const session = useSession();

  if (session.isPending) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner aria-label="Đang tải" />
      </div>
    );
  }
  if (!session.data?.user.is_superuser) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>Chỉ quản trị viên hệ thống mới vào được trang này.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-col gap-4 overflow-y-auto p-6">
      <header>
        <h1 className="font-semibold text-xl">Quản trị LLM</h1>
        <p className="text-muted-foreground text-sm">
          Kết nối, model và model dùng cho từng việc. Thay đổi có hiệu lực từ lượt trả lời tiếp
          theo.
        </p>
      </header>
      <Tabs defaultValue="assignments">
        <TabsList>
          <TabsTrigger value="assignments">Gán model</TabsTrigger>
          <TabsTrigger value="models">Model</TabsTrigger>
          <TabsTrigger value="connections">Kết nối</TabsTrigger>
        </TabsList>
        <TabsContent value="assignments">
          <AssignmentsPanel />
        </TabsContent>
        <TabsContent value="models">
          <ModelsPanel />
        </TabsContent>
        <TabsContent value="connections">
          <ConnectionsPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
