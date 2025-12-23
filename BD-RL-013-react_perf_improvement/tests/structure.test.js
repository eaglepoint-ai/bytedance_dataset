// tests/improvements.test.js
const fs = require("fs");
const path = require("path");

const projectRoot = process.cwd();

// Target repo is selected by env (same pattern you use in docker compose)
const targetRoot =
  process.env.PYTHONPATH && process.env.PYTHONPATH.trim() !== ""
    ? process.env.PYTHONPATH
    : path.join(projectRoot, "repository_before");

const sourcePath = path.join(targetRoot, "UserAnalyticsDashboard.jsx");
const source = fs.readFileSync(sourcePath, "utf8");

describe("UserAnalyticsDashboard structural improvements (FAIL_TO_PASS)", () => {
  test("visibleUsers does NOT create new derived objects in map", () => {
    // In the AFTER version these should be gone
    expect(source).not.toContain(".map((u) => ({");
    expect(source).not.toContain("label: `${u.name} (${u.score})`");
    expect(source).not.toContain("lastSeenText: formatLastActive(u.lastActive)");
  });

  test("visibleUsers only filters and sorts original user objects", () => {
    expect(source).toContain("return [...users]");
    expect(source).toContain(".filter((u) => u.name.toLowerCase().includes(q))");
    expect(source).toContain(".sort((a, b) => b.score - a.score)");
  });

  test("UserItem uses isSelected + formatLastActive and computes label/lastSeenText inside", () => {
    expect(source).toContain("const UserItem = memo(function UserItem");
    expect(source).toContain("({ user, isSelected, onSelect, formatLastActive })");
    expect(source).toContain("const label = `${user.name} (${user.score})`;");
    expect(source).toContain("const lastSeenText = formatLastActive(user.lastActive);");
    expect(source).toContain("background: isSelected ?");
  });
});
