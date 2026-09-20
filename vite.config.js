import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            "/api": {
                target: "http://localhost:8085",
                changeOrigin: true
            }
        }
    },
    test: {
        environment: "jsdom",
        globals: true,
        coverage: {
            provider: "v8",
            // lcov is required by SonarCloud (sonar.javascript.lcov.reportPaths).
            reporter: ["text", "lcov"]
        }
    }
});
