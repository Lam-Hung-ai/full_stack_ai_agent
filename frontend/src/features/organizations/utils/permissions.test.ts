import { describe, expect, it } from "vitest";
import { invitationAccountSchema } from "../schemas/organization.schema";
import { groupPermissions, roleLabel } from "./permissions";

const permission = (key: string) => {
  const [resource, action] = key.split(".");
  return { key, resource, action, description: null };
};

describe("groupPermissions", () => {
  it("groups by resource in catalog order with Vietnamese labels", () => {
    const groups = groupPermissions(
      ["conversation.create", "conversation.share", "tool.get_current_time", "x.y"].map(
        permission,
      ),
    );
    expect(groups.map((group) => [group.label, group.permissions.length])).toEqual([
      ["Chat", 2],
      ["Tool", 1],
      ["x", 1],
    ]);
  });
});

describe("roleLabel", () => {
  it("translates built-in roles and keeps custom names", () => {
    expect(roleLabel({ name: "Owner", role_key: "owner" })).toBe("Chủ sở hữu");
    expect(roleLabel({ name: "Kế toán", role_key: null })).toBe("Kế toán");
  });
});

describe("invitationAccountSchema", () => {
  it("needs a name and a confirmed password", () => {
    expect(
      invitationAccountSchema.safeParse({
        name: "Bình",
        password: "Str0ng!pass",
        confirm: "Str0ng!pass",
      }).success,
    ).toBe(true);
    expect(
      invitationAccountSchema.safeParse({ name: " ", password: "Str0ng!pass", confirm: "x" })
        .success,
    ).toBe(false);
  });
});
