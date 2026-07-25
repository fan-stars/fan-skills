---
name: f-base-project-initializer
description: Initialize a renamed Fan full-stack project from the fixed fan-base and fan-base-vben Gitee repositories. Use when the user wants to create a new Fan project from these templates, rename its backend/frontend directories, update Maven coordinates and database names, generate runtime scripts, or verify the cloned project can start.
---

# Fan Project Initializer

Initialize a new project from:

- `git@gitee.com:fan-stars/fan-base.git`
- `git@gitee.com:fan-stars/fan-base-vben.git`

## Required input

Obtain the target project name from the user before mutating files. Normalize it to lowercase kebab-case and confirm normalization when it changes the supplied value.

Derive:

```text
PROJECT_NAME=<user name>             # example: fan-idc
BACKEND_DIR=$PROJECT_NAME            # fan-idc
FRONTEND_DIR=$PROJECT_NAME-vben      # fan-idc-vben
MAVEN_GROUP_ID=cn.fanstars.$PROJECT_NAME
DATABASE_NAME=${PROJECT_NAME//-/_}   # fan_idc
```

Use the current workspace as the destination unless the user specifies another location. Refuse to overwrite existing non-empty target directories.

## Workflow

Track and report these phases:

```text
- [ ] Confirm names and destination
- [ ] Clone both templates
- [ ] Rename directories and configure remotes
- [ ] Update backend Maven coordinates
- [ ] Update database and related configuration
- [ ] Inspect and resolve remaining template names
- [ ] Clean-build the backend
- [ ] Generate root runtime scripts when available
- [ ] Generate a root AGENTS.md when available
- [ ] Start and verify available applications
```

### 1. Clone and rename

Clone both repositories into temporary template directory names, then rename them to `BACKEND_DIR` and `FRONTEND_DIR`.

For both repositories:

1. Rename remote `origin` to `fan-base`.
2. Unset the current branch upstream so the destination remote can be decided later.
3. Do not push or create a new remote unless the user supplies it.

### 2. Update Maven coordinates

Follow this invariant:

- Root parent project:
  - `groupId` = `MAVEN_GROUP_ID`
  - `artifactId` = `PROJECT_NAME`
- Executable module remains `fan-server`:
  - directory remains `fan-server/`
  - module `artifactId` remains `fan-server`
  - output remains `fan-server.jar`

Apply the coordinate migration to every tracked `pom.xml`:

1. Replace internal `cn.fanstars.base` group IDs with `MAVEN_GROUP_ID`.
2. Replace root/parent references from `fan-base` to `PROJECT_NAME`.
3. Preserve external dependency group IDs.
4. Preserve all module artifact IDs except the root parent artifact.

Inspect the diff after the mechanical replacement. In particular, verify:

```xml
<!-- root pom.xml -->
<groupId>cn.fanstars.<project-name></groupId>
<artifactId><project-name></artifactId>

<!-- fan-server/pom.xml -->
<parent>
  <groupId>cn.fanstars.<project-name></groupId>
  <artifactId><project-name></artifactId>
</parent>
<artifactId>fan-server</artifactId>
```

### 3. Update database and related names

Change the template database `fan_base` to `DATABASE_NAME` in:

- `fan-server/src/main/resources/application-local.yaml`
- `fan-server/src/main/resources/application-dev.yaml`
- relevant SQL comments, bootstrap scripts, Docker files, and documentation

Update Docker defaults:

- `container_name` to `PROJECT_NAME`
- `--spring.application.name` to `PROJECT_NAME`

Do not create, rename, copy, or delete an actual database without explicit authorization. If startup reports `Unknown database`, tell the user to create it or request permission for a migration.

### 4. Audit remaining template names

Search tracked source/configuration files for:

```text
fan-base
fan_base
cn.fanstars.base
```

Exclude `.git`, build outputs, dependency directories, runtime logs, and caches. Classify every remaining match before changing it:

- Update project identity, internal Maven coordinates, database names, Docker names, and current docs.
- Keep remote URLs/names unless the user provides a destination remote.
- Do not rewrite unrelated historical text or third-party identifiers blindly.

### 5. Validate backend

Run from the backend repository root:

```bash
mvn clean
mvn -pl fan-server -am package -DskipTests
```

Require both commands to succeed. Confirm the artifact exists at:

```text
fan-server/target/fan-server.jar
```

### 6. Generate runtime scripts

If `$project-runtime-manager` is available, use it after the rename/configuration work:

1. Detect the backend and frontend again from their renamed paths.
2. Generate unified runtime management files in the workspace root `scripts/`, not inside either repository.
3. Ensure generated scripts reference `BACKEND_DIR`, `FRONTEND_DIR`, and `fan-server.jar`.
4. Keep local runtime overrides in root `scripts/config/`.
5. Do not overwrite either repository's existing `scripts/` content.

If the skill is unavailable, report that and generate nothing unless the user explicitly asks for a fallback implementation.

### 7. Generate root AGENTS.md

If `$create-agentsmd` is available, use it after the projects and runtime scripts have reached their final structure:

1. Create one unified `AGENTS.md` in the workspace root, not inside either repository, unless the user explicitly requests nested files.
2. Analyze the actual backend/frontend build, test, development, and runtime commands before documenting them.
3. Record these upstream relationships:
   - backend is based on `https://gitee.com/zhijiantianya/ruoyi-vue-pro`
   - Vben frontend is based on `https://gitee.com/yudaocode/yudao-ui-admin-vben`
4. Mark both `fan-base` remotes as read-only template sources. Prohibit pushing, creating remote branches/tags, pull requests, or setting the current branch to track them.
5. Allow project-specific local changes, but when a requested change belongs to the shared template or should be fixed in `fan-base`, stop that common portion and tell the user the affected template, files, and recommended change. Let the user modify the corresponding `fan-base` project, then continue after confirmation.
6. Document that any destination remote or remote mutation requires explicit user authorization.
7. Include the final directory names, Maven coordinate invariant, database safety boundary, root runtime scripts, external configuration paths, tests, and delivery checks.
8. Add a mandatory coding-time configuration rule based on `$project-runtime-manager`:
   - Do not modify existing project configuration files while implementing features or fixes. This includes `application*.yml|yaml`, `bootstrap*.yml|yaml`, `.env*`, `package.json`, `vite.config.*`, `nuxt.config.*`, `pom.xml`, `build.gradle*`, and `settings.gradle*`.
   - Read existing project configuration only to infer runtime values.
   - Put runtime overrides only in the workspace-root `scripts/config/` files defined by `$project-runtime-manager`, and load them through CLI arguments or environment variables from the root startup scripts.
   - Do not create a second configuration convention when suitable `scripts/config/` files already exist.
   - If the requested change genuinely requires altering dependency, build, or shared project configuration and cannot be represented as a runtime override, stop and explain the required file and reason to the user before editing it.
   - Clarify that this coding-time rule does not prevent the explicit one-time identity migration performed earlier by this initializer.

If a root `AGENTS.md` already exists, inspect it and update only missing or stale project instructions while preserving unrelated user-authored rules.

If `$create-agentsmd` is unavailable, report that and do not synthesize a substitute unless the user explicitly requests one.

### 8. Start and verify

When root startup scripts exist:

1. Start the backend and frontend with those scripts.
2. Keep the processes alive long enough to catch delayed initialization failures.
3. Run status scripts.
4. Verify inferred HTTP ports with local requests.
5. Inspect logs when a process exits after initially reporting success.

Treat a process as successfully started only when its process check and HTTP check both pass. A `401` application response with HTTP `200` is acceptable evidence that the backend and authentication chain are running.

If Bouncy Castle/JCE verification fails, prefer a standard JDK through root external runtime configuration. If the packaged provider still fails, use synchronized backend/frontend local overrides only after explaining the behavior change; do not edit repository application settings merely to hide the error.

## Completion report

Report:

1. Final backend/frontend directory names
2. Root Maven coordinates and preserved `fan-server` module coordinate
3. Database name and whether the physical database was touched
4. Files/categories changed
5. Clean/build results
6. Runtime script location
7. Root AGENTS.md location and upstream/remote safeguards recorded
8. Process IDs, ports, and HTTP verification results
9. Any remaining template identifiers and why they were intentionally retained
