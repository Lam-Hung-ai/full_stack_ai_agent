import { describe, expect, it } from "vitest";
import { authErrorMessage } from "../utils/error-message";
import { newPasswordSchema } from "./auth.schema";

describe("newPasswordSchema", () => {
  it("accepts a strong password typed twice", () => {
    const result = newPasswordSchema.safeParse({ password: "Str0ng!pass", confirm: "Str0ng!pass" });
    expect(result.success).toBe(true);
  });

  it("flags a mismatch on the confirmation field", () => {
    const result = newPasswordSchema.safeParse({ password: "Str0ng!pass", confirm: "Str0ng!pas" });
    expect(result.success).toBe(false);
    expect(result.error?.issues.map((issue) => issue.path)).toEqual([["confirm"]]);
  });

  it("applies the backend complexity rules", () => {
    const result = newPasswordSchema.safeParse({ password: "password", confirm: "password" });
    expect(result.success).toBe(false);
  });
});

describe("authErrorMessage for links", () => {
  it("names a spent link, also without a response", () => {
    expect(authErrorMessage({ code: "invalid_token" })).toBe(
      "Liên kết không hợp lệ, đã dùng hoặc đã hết hạn.",
    );
  });
});
