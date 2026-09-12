import {defineConfig} from "@playwright/test";
export default defineConfig({testDir:"tests/browser",testMatch:"cm2.spec.ts",workers:1,timeout:45000,use:{baseURL:"http://127.0.0.1:19093/tests/cm2-preview/",channel:"msedge",headless:true,trace:"retain-on-failure"},webServer:[
  {command:'"..\\..\\.venv\\Scripts\\python.exe" -m uvicorn scripts.preview_cm2_training:app --app-dir ../.. --host 127.0.0.1 --port 19092',url:"http://127.0.0.1:19092/health",reuseExistingServer:false},
  {command:"npx vite --config vite.cm2.config.mjs",url:"http://127.0.0.1:19093/tests/cm2-preview/",reuseExistingServer:false}
]});
