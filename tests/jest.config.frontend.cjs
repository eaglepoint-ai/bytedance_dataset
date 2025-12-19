module.exports = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.jsx?$": [
      "babel-jest",
      {
        presets: [
          ["@babel/preset-env", { targets: { node: "current" } }],
          ["@babel/preset-react", { runtime: "automatic" }],
        ],
      },
    ],
  },
  moduleNameMapper: {
    "\\.(css|less)$": "<rootDir>/mocks/styleMock.js",
    "^@/client/(.*)$": "<rootDir>/../repository_after/client/src/$1",
    "^react$": "<rootDir>/node_modules/react",
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testMatch: ["<rootDir>/frontend/**/*.test.js"],
};
