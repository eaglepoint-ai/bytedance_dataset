module.exports = {
  testEnvironment: "node",
  testMatch: ["<rootDir>/backend/**/*.test.js"],
  transform: {
    "^.+\\.jsx?$": [
      "babel-jest",
      {
        presets: [["@babel/preset-env", { targets: { node: "current" } }]],
      },
    ],
  },
  moduleNameMapper: {
    "^@/server/(.*)$": "<rootDir>/server/$1",
  },
};
