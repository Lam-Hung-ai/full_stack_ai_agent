import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api";
import { authErrorMessage } from "./error-message";
import { safeNext } from "./safe-next";

describe("safeNext", () => {
  it("accepts internal paths", () => {
    expect(safeNext("/chat?x=1")).toBe("/chat?x=1");
  });

  it.each([null, "", "https://evil.example", "//evil.example", "/\\evil.example", "chat"])(
    "rejects %s",
    (value) => {
      expect(safeNext(value)).toBe("/");
    },
  );
});

describe("authErrorMessage", () => {
  it("maps known codes and hides unknown ones", () => {
    expect(authErrorMessage(new ApiError(401, "invalid_credentials"))).toBe(
      "Email hoặc mật khẩu không đúng.",
    );
    expect(authErrorMessage(new ApiError(500, "internal_error"))).toBe(
      "Đã có lỗi xảy ra. Vui lòng thử lại.",
    );
  });
});
