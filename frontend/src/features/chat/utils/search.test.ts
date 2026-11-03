import { describe, expect, it } from "vitest";
import { highlight, searchTerm } from "./search";

describe("searchTerm", () => {
  it("collapses spaces and waits for two characters", () => {
    expect(searchTerm("  a ")).toBeNull();
    expect(searchTerm("  hà   nội ")).toBe("hà nội");
  });
});

describe("highlight", () => {
  it("marks every match ignoring accents and case", () => {
    expect(highlight("Mùa thu Hà Nội, hà nội đẹp", "ha noi")).toEqual([
      { text: "Mùa thu ", match: false },
      { text: "Hà Nội", match: true },
      { text: ", ", match: false },
      { text: "hà nội", match: true },
      { text: " đẹp", match: false },
    ]);
  });

  it("folds đ and keeps text without a match whole", () => {
    expect(highlight("Đà Lạt", "da lat")).toEqual([{ text: "Đà Lạt", match: true }]);
    expect(highlight("Không có", "xyz")).toEqual([{ text: "Không có", match: false }]);
  });
});
