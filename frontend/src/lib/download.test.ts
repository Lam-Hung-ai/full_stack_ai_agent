import { describe, expect, it } from "vitest";
import { attachmentName } from "./download";

describe("attachmentName", () => {
  it("reads the file name of an attachment", () => {
    expect(attachmentName('attachment; filename="chat-export-20261030.zip"', "x.zip")).toBe(
      "chat-export-20261030.zip",
    );
    expect(attachmentName("attachment; filename*=UTF-8''b%E1%BA%A3n.zip", "x.zip")).toBe("bản.zip");
    expect(
      attachmentName(
        "attachment; filename=\"Chat Ca nhan.zip\"; filename*=UTF-8''Chat%20C%C3%A1%20nh%C3%A2n.zip",
        "x.zip",
      ),
    ).toBe("Chat Cá nhân.zip");
    expect(attachmentName(null, "x.zip")).toBe("x.zip");
  });
});
