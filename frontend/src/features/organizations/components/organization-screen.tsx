"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSession } from "@/features/auth";
import { useOrganization } from "../hooks/use-organization";
import { organizationErrorMessage } from "../utils/error-message";
import { MANAGE } from "../utils/permissions";
import { InvitationsPanel } from "./invitations-panel";
import { MembersPanel } from "./members-panel";
import { OrganizationSettingsPanel } from "./organization-settings-panel";
import { RolesPanel } from "./roles-panel";

/** Organization admin: tabs appear by permission; the API checks every call. */
export function OrganizationScreen({ organizationId }: { organizationId: string }) {
  const organization = useOrganization(organizationId);
  const session = useSession();

  if (organization.isPending) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner aria-label="Đang tải tổ chức" />
      </div>
    );
  }
  if (organization.isError) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>{organizationErrorMessage(organization.error)}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const data = organization.data;
  const can = (permission: string) => data.permissions.includes(permission);
  const tabs = [
    can(MANAGE.members) && "members",
    can(MANAGE.members) && "invitations",
    can(MANAGE.roles) && "roles",
    "settings",
  ].filter((tab): tab is string => !!tab);

  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-col gap-4 overflow-y-auto p-6">
      <header className="flex items-center gap-2">
        <h1 className="font-semibold text-xl">{data.name}</h1>
        {data.is_owner && <Badge variant="secondary">Chủ sở hữu</Badge>}
      </header>
      <Tabs defaultValue={tabs[0]}>
        <TabsList>
          {tabs.includes("members") && <TabsTrigger value="members">Thành viên</TabsTrigger>}
          {tabs.includes("invitations") && <TabsTrigger value="invitations">Lời mời</TabsTrigger>}
          {tabs.includes("roles") && <TabsTrigger value="roles">Vai trò</TabsTrigger>}
          <TabsTrigger value="settings">Cài đặt</TabsTrigger>
        </TabsList>
        {tabs.includes("members") && (
          <TabsContent value="members">
            <MembersPanel
              canAssignRoles={can(MANAGE.roles)}
              currentUserId={session.data?.user.id ?? ""}
              organizationId={data.id}
            />
          </TabsContent>
        )}
        {tabs.includes("invitations") && (
          <TabsContent value="invitations">
            <InvitationsPanel organizationId={data.id} />
          </TabsContent>
        )}
        {tabs.includes("roles") && (
          <TabsContent value="roles">
            <RolesPanel organization={data} />
          </TabsContent>
        )}
        <TabsContent value="settings">
          <OrganizationSettingsPanel organization={data} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
