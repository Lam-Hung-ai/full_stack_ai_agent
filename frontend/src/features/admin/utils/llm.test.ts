import { describe, expect, it } from "vitest";
import { connectionSchema, modelSchema } from "../schemas/llm.schema";
import { addModel, moveModel, removeModel } from "./assignment";
import { formatSettings, parseSettings } from "./settings";

describe("settings", () => {
  it("parses a JSON object and treats empty as none", () => {
    expect(parseSettings('{"temperature": 0.2}')).toEqual({ temperature: 0.2 });
    expect(parseSettings("  ")).toEqual({});
  });

  it("refuses what is not an object", () => {
    expect(parseSettings("[1]")).toBeNull();
    expect(parseSettings("null")).toBeNull();
    expect(parseSettings("{oops")).toBeNull();
  });

  it("formats an empty object as empty text", () => {
    expect(formatSettings({})).toBe("");
    expect(parseSettings(formatSettings({ a: 1 }))).toEqual({ a: 1 });
  });
});

describe("assignment order", () => {
  it("adds once, removes, and moves within bounds", () => {
    expect(addModel(["a"], "b")).toEqual(["a", "b"]);
    expect(addModel(["a"], "a")).toEqual(["a"]);
    expect(removeModel(["a", "b"], "a")).toEqual(["b"]);
    expect(moveModel(["a", "b", "c"], 2, -1)).toEqual(["a", "c", "b"]);
    expect(moveModel(["a", "b"], 0, -1)).toEqual(["a", "b"]);
    expect(moveModel(["a", "b"], 1, 1)).toEqual(["a", "b"]);
  });
});

describe("form schemas", () => {
  const connection = {
    key: "openrouter",
    name: "OpenRouter",
    provider: "openrouter",
    clientParams: "",
    apiKey: "",
    clearApiKey: false,
    isActive: true,
  };

  it("accepts a valid connection and rejects a bad key or settings", () => {
    expect(connectionSchema.safeParse(connection).success).toBe(true);
    expect(connectionSchema.safeParse({ ...connection, key: "Open Router" }).success).toBe(false);
    expect(connectionSchema.safeParse({ ...connection, clientParams: "[1]" }).success).toBe(false);
  });

  it("requires a connection and a provider model name", () => {
    const model = {
      key: "claude",
      name: "Claude",
      connectionId: "",
      model: "",
      params: "",
      isActive: true,
    };
    const result = modelSchema.safeParse(model);
    expect(result.success).toBe(false);
    expect(result.error?.issues.map((issue) => issue.path[0])).toEqual(["connectionId", "model"]);
  });
});
