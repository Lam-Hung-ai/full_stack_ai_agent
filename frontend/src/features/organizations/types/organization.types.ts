import type { components } from "@/generated/api/schema";

type Schemas = components["schemas"];

export type Organization = Schemas["OrganizationResponse"];
export type Member = Schemas["MemberResponse"];
export type MemberList = Schemas["MemberListResponse"];
export type Invitation = Schemas["InvitationResponse"];
export type InvitationPreview = Schemas["InvitationPreview"];
export type JoinedOrganization = Schemas["JoinedOrganization"];
export type Role = Schemas["RoleResponse"];
export type RoleCreateInput = Schemas["RoleCreate"];
export type RoleUpdateInput = Schemas["RoleUpdate"];
export type Permission = Schemas["PermissionResponse"];
