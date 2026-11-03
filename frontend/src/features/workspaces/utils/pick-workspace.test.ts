import { describe, expect, it } from "vitest";
import type { Workspace } from "../types/workspace.types";
import { pickWorkspace, workspaceLabel } from "./pick-workspace";

const personal: Workspace = { id: "p", kind: "personal", name: null, organization_id: null };
const org: Workspace = { id: "o", kind: "organization", name: "Alpha", organization_id: "a" };

describe("pickWorkspace", () => {
  it("keeps the stored choice while it is still accessible", () => {
    expect(pickWorkspace([personal, org], "o")).toBe(org);
  });

  it("falls back to the personal workspace when access was lost", () => {
    expect(pickWorkspace([personal], "o")).toBe(personal);
    expect(pickWorkspace([org, personal], null)).toBe(personal);
  });

  it("labels workspaces", () => {
    expect(workspaceLabel(personal)).toBe("Cá nhân");
    expect(workspaceLabel(org)).toBe("Alpha");
  });
});
