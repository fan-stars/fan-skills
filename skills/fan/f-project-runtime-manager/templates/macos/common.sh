# macOS 进程库。生成时原样复制为 scripts/runtime/macos/lib/common.sh。
# 适用于 bash 3.2。这里没有项目名；身份和命令数组由 lib/app-<app>.sh 提供。

die() {
  echo "$*" >&2
  exit 1
}

runtime_prepare() {
  RUN_DIR="$SCRIPT_DIR/run"
  LOG_DIR="$SCRIPT_DIR/logs"
  CONFIG_DIR="$SCRIPT_DIR/config"
  PID_FILE="$RUN_DIR/${APP_NAME}.pid"
  LAUNCHER_FILE="$RUN_DIR/${APP_NAME}.launcher.pid"
  MODE_FILE="$RUN_DIR/${APP_NAME}.mode"
  LOG_FILE="$LOG_DIR/${APP_NAME}.log"
  ENV_FILE="$CONFIG_DIR/${APP_NAME}.env"
  EXAMPLE_FILE="$CONFIG_DIR/${APP_NAME}.env.example"
  if [[ "$APP_KIND" == "java" ]]; then
    REACTOR_DIR="$WORKSPACE_ROOT/$REACTOR_REL"
    UNIT_DIR="$WORKSPACE_ROOT/$UNIT_REL"
    JAR_PATH="$WORKSPACE_ROOT/$JAR_REL"
    if [[ -z "${APP_CMD_MARKER:-}" && -n "${MAIN_CLASS:-}" ]]; then
      APP_CMD_MARKER="$MAIN_CLASS"
    fi
    if [[ -n "${FINAL_NAME:-}" ]]; then
      APP_JAR_MARKER="target/${FINAL_NAME}.jar"
    fi
  else
    WORK_DIR="$WORKSPACE_ROOT/$WORK_REL"
    PACKAGE_DIR="$WORKSPACE_ROOT/$PACKAGE_REL"
  fi
  mkdir -p "$RUN_DIR" "$LOG_DIR" "$CONFIG_DIR"
}

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" && -f "$EXAMPLE_FILE" ]]; then
    cp "$EXAMPLE_FILE" "$ENV_FILE"
  fi
}

load_env_file() {
  local file="$1" line key value
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    [[ "$line" == *=* ]] || continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [[ -z "$value" || "$value" == "change-me" ]]; then
      continue
    fi
    export "$key=$value"
  done < "$file"
}

app_port() {
  local value=""
  if [[ -n "${APP_PORT_VAR:-}" ]]; then
    value="${!APP_PORT_VAR-}"
  fi
  if [[ -z "$value" || "$value" == "change-me" ]]; then
    value="${APP_PORT_DEFAULT:-}"
  fi
  printf '%s' "$value"
}

pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

read_pid_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  tr -d '[:space:]' < "$file"
}

process_cwd() {
  local pid="$1" path=""
  if [[ -r "/proc/$pid/cwd" || -L "/proc/$pid/cwd" ]]; then
    path="$(readlink "/proc/$pid/cwd" 2>/dev/null || true)"
  else
    path="$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true)"
  fi
  printf '%s' "$path"
}

process_cmd() {
  local pid="$1"
  if [[ -r "/proc/$pid/cmdline" ]]; then
    tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true
    return 0
  fi
  ps -p "$pid" -ww -o command= 2>/dev/null || true
}

is_scan_tool() {
  local cmd="$1"
  case "$cmd" in
    pgrep*|*/pgrep\ *|*\ pgrep\ *)
      return 0
      ;;
  esac
  return 1
}

cwd_is() {
  local cwd="$1" dir="$2"
  [[ -n "$dir" && ( "$cwd" == "$dir" || "$cwd" == "$dir/"* ) ]]
}

process_matches() {
  local pid="$1" cmd cwd
  pid_alive "$pid" || return 1
  cmd="$(process_cmd "$pid")"
  is_scan_tool "$cmd" && return 1
  cwd="$(process_cwd "$pid")"
  if [[ "$APP_KIND" == "java" ]]; then
    if [[ -n "${APP_CMD_MARKER:-}" && "$cmd" == *"$APP_CMD_MARKER"* ]]; then
      cwd_is "$cwd" "$UNIT_DIR"
      return $?
    fi
    if [[ -n "${APP_JAR_MARKER:-}" && "$cmd" == *"$APP_JAR_MARKER"* ]]; then
      [[ "$cwd" == "$REACTOR_DIR" || "$cwd" == "$UNIT_DIR" || "$cwd" == "$UNIT_DIR/"* ]]
      return $?
    fi
    return 1
  fi
  [[ -n "${APP_CMD_MARKER:-}" && "$cmd" == *"$APP_CMD_MARKER"* ]] || return 1
  [[ "$cwd" == "$PACKAGE_DIR" ]]
}

launcher_matches() {
  local pid="$1" cmd cwd
  pid_alive "$pid" || return 1
  cmd="$(process_cmd "$pid")"
  is_scan_tool "$cmd" && return 1
  cwd="$(process_cwd "$pid")"
  if [[ "$APP_KIND" == "java" ]]; then
    [[ "$cwd" == "$REACTOR_DIR" ]] || return 1
    [[ "$cmd" == *mvn* || "$cmd" == *gradle* || "$cmd" == *classworlds* ]]
    return $?
  fi
  [[ -n "${NODE_PM:-}" ]] || return 1
  [[ "$cwd" == "$WORK_DIR" || "$cwd" == "$PACKAGE_DIR" ]] || return 1
  [[ "$cmd" == *"$NODE_PM"* ]]
}

descendants_of() {
  local root="$1"
  local snapshot pid ppid seen changed=1
  [[ -n "$root" ]] || return 0
  seen=" $root "
  snapshot="$(ps -axww -o pid=,ppid= 2>/dev/null || true)"
  while [[ "$changed" -eq 1 ]]; do
    changed=0
    while read -r pid ppid; do
      [[ -n "${pid:-}" ]] || continue
      if [[ "$seen" == *" $ppid "* && "$seen" != *" $pid "* ]]; then
        seen="$seen$pid "
        changed=1
      fi
    done <<< "$snapshot"
  done
  for pid in $seen; do
    [[ "$pid" == "$root" ]] && continue
    printf '%s\n' "$pid"
  done
}

find_matching_pids() {
  local launcher="${1:-}" pid marker cmd result=""
  if [[ -n "$launcher" ]]; then
    for pid in $(descendants_of "$launcher"); do
      [[ "$pid" == "$launcher" ]] && continue
      if process_matches "$pid"; then
        case " $result " in
          *" $pid "*) ;;
          *) result="$result $pid" ;;
        esac
      fi
    done
    printf '%s' "${result# }"
    return 0
  fi
  if command -v pgrep >/dev/null 2>&1; then
    for marker in "${APP_CMD_MARKER:-}" "${APP_JAR_MARKER:-}"; do
      [[ -n "$marker" ]] || continue
      for pid in $(pgrep -f "$marker" 2>/dev/null || true); do
        [[ "$pid" == "$$" ]] && continue
        cmd="$(process_cmd "$pid")"
        is_scan_tool "$cmd" && continue
        if process_matches "$pid"; then
          case " $result " in
            *" $pid "*) ;;
            *) result="$result $pid" ;;
          esac
        fi
      done
    done
    printf '%s' "${result# }"
    return 0
  fi
  while read -r pid cmd; do
    [[ -n "${pid:-}" ]] || continue
    [[ "$pid" == "$$" ]] && continue
    is_scan_tool "$cmd" && continue
    if process_matches "$pid"; then
      result="$result $pid"
    fi
  done < <(ps -axww -o pid=,command= 2>/dev/null || true)
  printf '%s' "${result# }"
}

word_count() {
  local value="$1"
  [[ -n "$value" ]] || { echo 0; return 0; }
  # shellcheck disable=SC2086
  set -- $value
  echo $#
}

stop_pid() {
  local pid="$1" waited=0
  pid_alive "$pid" || return 0
  echo "stopping pid $pid" >&2
  kill -TERM "$pid" 2>/dev/null || true
  while [[ "$waited" -lt 25 ]]; do
    pid_alive "$pid" || return 0
    sleep 1
    waited=$((waited + 1))
  done
  kill -KILL "$pid" 2>/dev/null || true
  sleep 1
  if pid_alive "$pid"; then
    return 1
  fi
  return 0
}

stop_parents_of() {
  local pid="$1" parent next guard=0
  parent="$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d '[:space:]' || true)"
  stop_pid "$pid" || return 1
  while [[ -n "$parent" && "$parent" != "0" && "$parent" != "1" && "$guard" -lt 8 ]]; do
    next="$(ps -p "$parent" -o ppid= 2>/dev/null | tr -d '[:space:]' || true)"
    if launcher_matches "$parent"; then
      stop_pid "$parent" || return 1
    else
      break
    fi
    parent="$next"
    guard=$((guard + 1))
  done
  return 0
}

runtime_stop() {
  local pid launcher found count left
  runtime_prepare
  pid="$(read_pid_file "$PID_FILE")"
  launcher="$(read_pid_file "$LAUNCHER_FILE")"
  if [[ -n "$pid" ]] && pid_alive "$pid" && process_matches "$pid"; then
    stop_parents_of "$pid" || die "$APP_NAME 停止失败"
  elif [[ -n "$pid" ]] && pid_alive "$pid"; then
    echo "$APP_NAME 的 pid $pid 与应用命令行或工作目录不符，未停止该进程" >&2
  else
    found="$(find_matching_pids)"
    count="$(word_count "$found")"
    if [[ "$count" -gt 1 ]]; then
      echo "$APP_NAME 匹配到多个进程，未停止: $found" >&2
      exit 1
    fi
    if [[ "$count" -eq 1 ]]; then
      stop_parents_of "$found" || die "$APP_NAME 停止失败"
    fi
  fi
  if [[ -n "$launcher" ]] && pid_alive "$launcher" && launcher_matches "$launcher"; then
    stop_pid "$launcher" || die "$APP_NAME 启动器停止失败"
  fi
  rm -f "$PID_FILE" "$LAUNCHER_FILE"
  left="$(find_matching_pids)"
  if [[ -n "$left" ]]; then
    echo "$APP_NAME 停止后仍有进程: $left" >&2
    exit 1
  fi
  echo "$APP_NAME: stopped"
}

port_pids() {
  local port="$1"
  [[ -n "$port" ]] || return 0
  command -v lsof >/dev/null 2>&1 || return 0
  lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | sort -u || true
}

port_conflict_pids() {
  local port="$1" pid out=""
  for pid in $(port_pids "$port"); do
    if process_matches "$pid"; then
      continue
    fi
    out="$out $pid"
  done
  printf '%s' "${out# }"
}

pid_list_contains() {
  local needle="$1" list="$2" pid
  for pid in $list; do
    [[ "$pid" == "$needle" ]] && return 0
  done
  return 1
}

refuse_port_conflict() {
  local port conflicts
  port="$(app_port)"
  [[ -n "$port" ]] || return 0
  conflicts="$(port_conflict_pids "$port")"
  if [[ -n "$conflicts" ]]; then
    die "端口 $port 已被其他 PID 占用: $conflicts"
  fi
}

tail_log() {
  if [[ -f "$LOG_FILE" ]]; then
    echo "last lines of $LOG_FILE:" >&2
    tail -n 80 "$LOG_FILE" >&2 || true
  fi
}

launch_in_session() {
  local logfile="$1"
  shift
  [[ $# -gt 0 ]] || die "缺少启动命令"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$logfile" "$@" <<'PY'
import os
import sys

logfile = sys.argv[1]
cmd = sys.argv[2:]
fd = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
pid = os.fork()
if pid == 0:
    try:
        os.setsid()
    except OSError:
        pass
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    try:
        os.execvpe(cmd[0], cmd, os.environ)
    except OSError:
        os._exit(127)
os.close(fd)
sys.stdout.write(str(pid) + "\n")
sys.stdout.flush()
PY
    return 0
  fi
  if command -v setsid >/dev/null 2>&1; then
    setsid "$@" >>"$logfile" 2>&1 </dev/null &
    printf '%s\n' "$!"
    return 0
  fi
  die "需要 python3 才能把进程放入新会话"
}

valid_pid() {
  local pid="$1"
  case "$pid" in
    ''|*[!0-9]*)
      return 1
      ;;
  esac
  return 0
}

fail_launcher() {
  local launcher="$1"
  echo "$APP_NAME 未能在 60 秒内确认唯一的应用进程" >&2
  if valid_pid "$launcher" && pid_alive "$launcher"; then
    stop_pid "$launcher" || true
  fi
  rm -f "$PID_FILE" "$LAUNCHER_FILE" "$MODE_FILE"
  tail_log
  exit 1
}

wait_for_descendant() {
  local launcher="$1" elapsed=0 found count
  while [[ "$elapsed" -lt 60 ]]; do
    found="$(find_matching_pids "$launcher")"
    count="$(word_count "$found")"
    if [[ "$count" -eq 1 ]]; then
      printf '%s\n' "$found" > "$PID_FILE"
      printf 'run\n' > "$MODE_FILE"
      printf '%s' "$found"
      return 0
    fi
    if [[ "$count" -gt 1 ]]; then
      echo "$APP_NAME 匹配到多个子孙进程: $found" >&2
      fail_launcher "$launcher"
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  fail_launcher "$launcher"
}

port_wait_limit() {
  local raw=""
  raw="${PORT_WAIT_SECONDS-}"
  case "$raw" in
    ''|change-me)
      printf '180\n'
      return 0
      ;;
  esac
  case "$raw" in
    *[!0-9]*|0*)
      printf '180\n'
      return 0
      ;;
  esac
  printf '%s\n' "$raw"
}

confirm_port() {
  local pid="$1" port="" elapsed=0 holders="" limit=""
  port="$(app_port)"
  [[ -n "$port" ]] || return 0
  limit="$(port_wait_limit)"
  while [[ "$elapsed" -lt "$limit" ]]; do
    if ! pid_alive "$pid"; then
      rm -f "$PID_FILE" "$LAUNCHER_FILE" "$MODE_FILE"
      tail_log
      die "$APP_NAME 在监听端口 $port 前退出"
    fi
    holders="$(port_pids "$port")"
    if pid_list_contains "$pid" "$holders"; then
      echo "port $port is listening (pid $pid)"
      return 0
    fi
    if [[ -n "$holders" ]]; then
      die "端口 $port 由其他 PID 监听: $holders"
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  if ! pid_alive "$pid"; then
    rm -f "$PID_FILE" "$LAUNCHER_FILE" "$MODE_FILE"
    tail_log
    die "$APP_NAME 在监听端口 $port 前退出"
  fi
  die "端口 $port 在 ${limit} 秒内尚未监听，进程 $pid 仍保留"
}

java_major_of() {
  local home="$1" version major
  [[ -n "$home" && -x "$home/bin/java" ]] || return 1
  version="$("$home/bin/java" -version 2>&1 | awk -F'"' '/version/ { print $2; exit }')"
  [[ -n "$version" ]] || return 1
  case "$version" in
    1.*)
      major="$(printf '%s' "$version" | sed 's/^1\.//; s/[^0-9].*$//')"
      ;;
    *)
      major="${version%%.*}"
      ;;
  esac
  case "$major" in
    ''|*[!0-9]*)
      return 1
      ;;
  esac
  printf '%s\n' "$major"
}

java_home_ok() {
  local home="$1" required="$2" major
  major="$(java_major_of "$home" 2>/dev/null || true)"
  [[ -n "$major" ]] || return 1
  if [[ -n "$required" && "$major" -lt "$required" ]]; then
    return 1
  fi
  printf '%s\n' "$home"
}

resolve_java_home() {
  local required="$1" cand major best="" best_major=999
  if [[ -n "${JAVA_HOME:-}" ]]; then
    cand="$(java_home_ok "$JAVA_HOME" "$required" || true)"
    if [[ -n "$cand" ]]; then
      printf '%s\n' "$cand"
      return 0
    fi
  fi
  [[ -n "$required" ]] || return 1
  if [[ -x /usr/libexec/java_home ]]; then
    cand="$(/usr/libexec/java_home -v "$required" 2>/dev/null || true)"
    if [[ -n "$cand" ]]; then
      printf '%s\n' "$cand"
      return 0
    fi
  fi
  for cand in \
    /Library/Java/JavaVirtualMachines/*/Contents/Home \
    "$HOME"/Library/Java/JavaVirtualMachines/*/Contents/Home \
    /opt/homebrew/opt/openjdk*/libexec/openjdk.jdk/Contents/Home \
    "$HOME"/.sdkman/candidates/java/* \
    /usr/lib/jvm/*; do
    [[ -d "$cand" && -x "$cand/bin/java" ]] || continue
    major="$(java_major_of "$cand" 2>/dev/null || true)"
    [[ -n "$major" && "$major" -ge "$required" && "$major" -lt "$best_major" ]] || continue
    best="$cand"
    best_major="$major"
  done
  [[ -n "$best" ]] || return 1
  printf '%s\n' "$best"
}

setup_java() {
  local home required="${JAVA_REQUIRED:-}"
  [[ "$APP_KIND" == "java" ]] || return 0
  [[ -n "$required" || -n "${JAVA_HOME:-}" ]] || return 0
  home="$(resolve_java_home "$required" || true)"
  if [[ -z "$home" ]]; then
    die "找不到 JDK ${required}+；把 JAVA_HOME 写到 $ENV_FILE"
  fi
  export JAVA_HOME="$home"
  export PATH="$JAVA_HOME/bin:$PATH"
  echo "JAVA_HOME=$JAVA_HOME"
}

run_logged() {
  if ! "$@" >>"$LOG_FILE" 2>&1; then
    tail_log
    die "命令失败: $*"
  fi
}

array_ready() {
  local name="$1"
  declare -p "$name" >/dev/null 2>&1
}

start_java_run() {
  local app_pid
  [[ -d "$REACTOR_DIR" ]] || die "缺少目录 $REACTOR_DIR"
  cd "$REACTOR_DIR"
  if array_ready JAVA_PREPARE_ARGV && [[ "${#JAVA_PREPARE_ARGV[@]}" -gt 0 ]]; then
    run_logged "${JAVA_PREPARE_ARGV[@]}"
  fi
  array_ready JAVA_RUN_ARGV || die "缺少 JAVA_RUN_ARGV"
  [[ "${#JAVA_RUN_ARGV[@]}" -gt 0 ]] || die "缺少 JAVA_RUN_ARGV"
  app_pid="$(launch_in_session "$LOG_FILE" "${JAVA_RUN_ARGV[@]}")"
  valid_pid "$app_pid" || die "$APP_NAME 启动失败"
  printf '%s\n' "$app_pid" > "$LAUNCHER_FILE"
  wait_for_descendant "$app_pid" >/dev/null
}

start_java_jar() {
  local app_pid cmd=()
  [[ -d "$REACTOR_DIR" ]] || die "缺少目录 $REACTOR_DIR"
  cd "$REACTOR_DIR"
  array_ready JAVA_PACKAGE_ARGV || die "缺少 JAVA_PACKAGE_ARGV"
  run_logged "${JAVA_PACKAGE_ARGV[@]}"
  [[ -f "$JAR_PATH" ]] || die "打包后找不到 $JAR_PATH"
  cmd=(java)
  if [[ -n "${JAVA_OPTS:-}" && "$JAVA_OPTS" != "change-me" ]]; then
    # JAVA_OPTS 按空白拆成多个 JVM 参数。
    # shellcheck disable=SC2206
    cmd+=($JAVA_OPTS)
  fi
  cmd+=(-jar "$JAR_PATH")
  rm -f "$LAUNCHER_FILE"
  app_pid="$(launch_in_session "$LOG_FILE" "${cmd[@]}")"
  valid_pid "$app_pid" || die "$APP_NAME 启动失败"
  printf '%s\n' "$app_pid" > "$PID_FILE"
  printf 'jar\n' > "$MODE_FILE"
  sleep 1
  if ! pid_alive "$app_pid" || ! process_matches "$app_pid"; then
    rm -f "$PID_FILE" "$MODE_FILE"
    tail_log
    die "$APP_NAME jar 进程没有留下来"
  fi
}

start_node() {
  local app_pid
  [[ -d "$WORK_DIR" ]] || die "缺少目录 $WORK_DIR"
  [[ -d "$PACKAGE_DIR" ]] || die "缺少目录 $PACKAGE_DIR"
  [[ -n "${APP_CMD_MARKER:-}" ]] || die "缺少 APP_CMD_MARKER"
  cd "$WORK_DIR"
  if [[ -z "${NODE_PM:-}" ]] && array_ready NODE_ARGV && [[ "${#NODE_ARGV[@]}" -gt 0 ]]; then
    NODE_PM="${NODE_ARGV[0]}"
  fi
  if [[ ! -d "$WORK_DIR/node_modules" ]]; then
    [[ -n "${NODE_PM:-}" ]] || die "缺少 NODE_PM"
    run_logged "$NODE_PM" install
  fi
  array_ready NODE_ARGV || die "缺少 NODE_ARGV"
  app_pid="$(launch_in_session "$LOG_FILE" "${NODE_ARGV[@]}")"
  valid_pid "$app_pid" || die "$APP_NAME 启动失败"
  printf '%s\n' "$app_pid" > "$LAUNCHER_FILE"
  wait_for_descendant "$app_pid" >/dev/null
}

print_running() {
  local mode pid launcher port
  mode="$(tr -d '[:space:]' < "$MODE_FILE" 2>/dev/null || echo unknown)"
  pid="$(read_pid_file "$PID_FILE")"
  launcher="$(read_pid_file "$LAUNCHER_FILE")"
  port="$(app_port)"
  echo "$APP_NAME mode=$mode pid=${pid:-none} launcher=${launcher:-none} port=${port:-none} log=$LOG_FILE config=$ENV_FILE"
}

usage_and_exit() {
  if [[ "$APP_KIND" == "java" ]]; then
    echo "用法: $(basename "$0") [run|jar]" >&2
  else
    echo "用法: $(basename "$0") [run]" >&2
  fi
  exit 2
}

runtime_start() {
  local mode="run" app_pid=""
  runtime_prepare
  if [[ $# -ge 1 ]]; then
    mode="$1"
  fi
  case "$mode" in
    run|jar) ;;
    *) usage_and_exit ;;
  esac
  if [[ "$APP_KIND" != "java" && "$mode" == "jar" ]]; then
    echo "$APP_NAME 没有 jar 模式" >&2
    usage_and_exit
  fi
  runtime_stop
  ensure_env_file
  load_env_file "$ENV_FILE"
  setup_java
  refuse_port_conflict
  printf '\n===== %s %s =====\n' "$mode" "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
  if [[ "$APP_KIND" == "java" && "$mode" == "jar" ]]; then
    start_java_jar
    app_pid="$(read_pid_file "$PID_FILE")"
  elif [[ "$APP_KIND" == "java" ]]; then
    start_java_run
    app_pid="$(read_pid_file "$PID_FILE")"
  else
    start_node
    app_pid="$(read_pid_file "$PID_FILE")"
  fi
  confirm_port "$app_pid"
  if [[ -n "$(app_port)" ]]; then
    print_running
  fi
}

runtime_restart() {
  local mode="run"
  runtime_prepare
  if [[ $# -ge 1 ]]; then
    case "$1" in
      run|jar) mode="$1" ;;
      *) usage_and_exit ;;
    esac
  elif [[ -f "$MODE_FILE" ]]; then
    mode="$(tr -d '[:space:]' < "$MODE_FILE")"
  fi
  if [[ "$APP_KIND" != "java" && "$mode" == "jar" ]]; then
    echo "$APP_NAME 没有 jar 模式" >&2
    usage_and_exit
  fi
  runtime_start "$mode"
}

runtime_status() {
  local pid
  runtime_prepare
  ensure_env_file
  load_env_file "$ENV_FILE"
  pid="$(read_pid_file "$PID_FILE")"
  if [[ -n "$pid" ]] && pid_alive "$pid" && process_matches "$pid"; then
    print_running
    return 0
  fi
  echo "$APP_NAME: stopped port=$(app_port)"
}
