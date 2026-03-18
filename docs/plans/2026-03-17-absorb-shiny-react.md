# Absorb @posit/shiny-react Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Vendor the @posit/shiny-react TypeScript source into `js/src/shiny-react/`, remove the npm dependency, and verify the build is functionally equivalent.

**Architecture:** Copy 9 TypeScript source files + LICENSE from `github.com/wch/shiny-react` (commit `4690978`) into `js/src/shiny-react/`. Update the single import in `js/src/index.ts` to point to the local path. Remove the npm dependency.

**Tech Stack:** TypeScript, Vite (IIFE build), React 19

---

### Task 1: Copy vendored source files

**Files:**
- Create: `js/src/shiny-react/LICENSE`
- Create: `js/src/shiny-react/index.ts`
- Create: `js/src/shiny-react/ImageOutput.tsx`
- Create: `js/src/shiny-react/get-shiny.ts`
- Create: `js/src/shiny-react/input-registry.ts`
- Create: `js/src/shiny-react/message-registry.ts`
- Create: `js/src/shiny-react/output-registry.ts`
- Create: `js/src/shiny-react/react-registry.ts`
- Create: `js/src/shiny-react/use-shiny.ts`
- Create: `js/src/shiny-react/utils.ts`

**Step 1: Clone upstream and copy files**

```bash
cd /tmp
git clone --depth 1 https://github.com/wch/shiny-react.git shiny-react-vendor
mkdir -p js/src/shiny-react
cp /tmp/shiny-react-vendor/LICENSE js/src/shiny-react/
cp /tmp/shiny-react-vendor/src/*.ts /tmp/shiny-react-vendor/src/*.tsx js/src/shiny-react/
rm -rf /tmp/shiny-react-vendor
```

**Step 2: Verify all 10 files are present**

```bash
ls js/src/shiny-react/
```

Expected: LICENSE, ImageOutput.tsx, get-shiny.ts, index.ts, input-registry.ts, message-registry.ts, output-registry.ts, react-registry.ts, use-shiny.ts, utils.ts

**Step 3: Commit**

```bash
git add js/src/shiny-react/
git commit -m "feat: vendor @posit/shiny-react source (commit 4690978)

Copy TypeScript source from github.com/wch/shiny-react into
js/src/shiny-react/ with MIT LICENSE for attribution."
```

---

### Task 2: Update imports and remove npm dependency

**Files:**
- Modify: `js/src/index.ts:16-22` — change import path
- Modify: `js/package.json:14` — remove `@posit/shiny-react` dependency

**Step 1: Update import in index.ts**

Change line 16-22 from:

```typescript
import {
  useShinyInput,
  useShinyOutput,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
} from "@posit/shiny-react";
```

To:

```typescript
import {
  useShinyInput,
  useShinyOutput,
  useShinyMessageHandler,
  useShinyInitialized,
  ImageOutput,
} from "./shiny-react";
```

**Step 2: Remove @posit/shiny-react from package.json dependencies**

In `js/package.json`, remove the line:

```json
    "@posit/shiny-react": "^0.0.16",
```

**Step 3: Run npm install to clean up node_modules**

```bash
cd js && npm install
```

Expected: lockfile updates, `node_modules/@posit/shiny-react/` is removed.

**Step 4: Commit**

```bash
git add js/src/index.ts js/package.json js/package-lock.json
git commit -m "refactor: replace @posit/shiny-react npm dep with vendored source

Update import in index.ts to ./shiny-react and remove the npm dependency."
```

---

### Task 3: Build and verify

**Files:**
- No new files — verification only

**Step 1: Type-check**

```bash
cd js && npm run lint
```

Expected: No errors. If there are type errors related to `@posit/shiny` type imports (used by vendored code for `ShinyClass` and `EventPriority`), these should resolve since `@posit/shiny` is already a devDependency.

**Step 2: Build**

```bash
cd js && npm run build
```

Expected: Vite build succeeds, `js/dist/shinyjson.js` and `js/dist/shinyjson.css` are produced.

**Step 3: Update dist copies in Python and R packages**

```bash
make update-dist
```

Expected: Built assets copied to `pkg-py/src/shinyjson/www/` and `pkg-r/inst/lib/shiny/`.

**Step 4: Run Python tests**

```bash
make py-check-tests
```

Expected: All tests pass.

**Step 5: Commit updated dist**

```bash
git add js/dist/ pkg-py/src/shinyjson/www/ pkg-r/inst/lib/shiny/
git commit -m "chore: rebuild dist with vendored shiny-react source"
```

---

### Task 4: Smoke test the example app

**Files:**
- No changes — manual verification

**Step 1: Start the example app**

```bash
uv run shiny run examples/hello-shinyjson/app.py --port 8765
```

**Step 2: Verify in browser**

Open http://127.0.0.1:8765 and confirm:
- Page loads without console errors
- Card with title renders
- Badges appear when slider > 0
- Badge variant changes when select is changed
- Button click increments the counter
- All sidebar inputs update the output reactively

**Step 3: Stop the app**

Ctrl+C or kill the process.
