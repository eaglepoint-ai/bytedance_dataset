// tests/equivalence.test.js
const fs = require("fs");
const path = require("path");

const projectRoot = process.cwd();
const beforePath = path.join(projectRoot, "repository_before", "UserAnalyticsDashboard.jsx");
const afterPath = path.join(projectRoot, "repository_after", "UserAnalyticsDashboard.jsx");

const beforeSource = fs.readFileSync(beforePath, "utf8");
const afterSource = fs.readFileSync(afterPath, "utf8");

describe("Equivalence smoke checks for before/after", () => {
  test("both keep the FIXED_CHECKSUM loop", () => {
    const loopSnippet = "for (let i = 0; i < 50_000_000; i++)";
    expect(beforeSource).toContain(loopSnippet);
    expect(afterSource).toContain(loopSnippet);
  });

  test("both export default UserAnalyticsDashboard", () => {
    const sig = "export default function UserAnalyticsDashboard()";
    expect(beforeSource).toContain(sig);
    expect(afterSource).toContain(sig);
  });
});