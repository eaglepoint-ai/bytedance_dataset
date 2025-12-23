const fs = require("fs");
const path = require("path");

function main() {
  const projectRoot = process.cwd();
  const beforePath = path.join(projectRoot, "repository_before", "UserAnalyticsDashboard.jsx");
  const afterPath = path.join(projectRoot, "repository_after", "UserAnalyticsDashboard.jsx");

  const beforeSource = fs.readFileSync(beforePath, "utf8");
  const afterSource = fs.readFileSync(afterPath, "utf8");

  const results = {
    before_lines: beforeSource.split(/\r?\n/).length,
    after_lines: afterSource.split(/\r?\n/).length,
    before_has_map_with_spread: beforeSource.includes(".map((u) => ({"),
    after_has_map_with_spread: afterSource.includes(".map((u) => ({"),
    after_uses_isSelected: afterSource.includes("isSelected"),
    after_moves_label_computation: afterSource.includes("const label = `${user.name} (${user.score})`;")
  };

  const outPath = path.join(projectRoot, "evaluation", "results.json");
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), "utf8");
  console.log(JSON.stringify(results, null, 2));
}

if (require.main === module) {
  main();
}
