import {defineConfig} from "vite";
import path from "node:path";
export default defineConfig({resolve:{alias:{"@":path.resolve("src")}},esbuild:{jsx:"automatic"},server:{host:"127.0.0.1",port:19093,strictPort:true,proxy:{"/api":"http://127.0.0.1:19092"}}});
