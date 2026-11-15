#!/usr/bin/env bash
# =====================================================================
# berjaya-deploy_v0.2.sh
# Deploy the Berjaya interface (develop) to the test server and check it.
# Version: v0.2   Date: 2026-11-15   Site: sidra.local
#
# Run as root on the test server, inside tmux (the provider has cut
# sessions before):
#   tmux new -s deploy
#   bash /root/berjaya-deploy_v0.2.sh            # deploy, then check
#
# Other modes:
#   bash berjaya-deploy_v0.2.sh check            # checks only, changes nothing
#   bash berjaya-deploy_v0.2.sh brand            # put the Berjaya logo back on
#                                                # the sign-in page and navbar
#                                                # (only when `check` says it is
#                                                # not ours), then clear caches
#   bash berjaya-deploy_v0.2.sh rollback <commit>
#                                                # code back to <commit>; prints,
#                                                # but never runs, the DB restore
#
# WHAT `deploy` DOES, IN ORDER
#   1 preflight   root, bench, git checkout, disk space, folder access
#   2 backup      bench backup --with-files. If it fails, nothing else runs.
#   3 code        fast-forward the app to develop. Local changes or a
#                 diverged branch stop the script; nothing is discarded.
#   4 build       yarn install (frozen lockfile) + bench build --force for the app
#   5 migrate     bench migrate (also re-applies branding settings)
#   6 restart     clear caches, restart the bench processes
#   7 check       the same checks as `check` mode
#
# RULES ENFORCED
#   * Backup first; the backup paths are written to the log and to
#     /root/berjaya-deploy-last.txt for rollback.
#   * The git stash is never applied or dropped.
#   * No Company, contract or ledger record is changed. The timeline
#     check only reads.
#   * The database is never restored by this script.
#   * On any refusal or error it stops and prints the message.
#   * Anything it cannot establish is reported NOT VERIFIED, never PASS.
# =====================================================================
set -uo pipefail

SITE=sidra.local
BENCH=/home/frappe/sidra/frappe-bench
APP=sidra_realestate
FRAPPE_USER=frappe
BRANCH=develop
BASE_URL=http://127.0.0.1           # nginx on this server; sidra.local is the default site
CONTRACT=SSC-2026-00055             # registered External contract on the test site
MIN_FREE_GB=3
LOG=/root/berjaya-deploy.log
STATE=/root/berjaya-deploy-last.txt
TIMELINE_OUT=/root/berjaya-timeline-$CONTRACT.json

LOGO=/assets/sidra_realestate/images/berjaya-wordmark.png
FAVICON=/assets/sidra_realestate/images/berjaya-favicon.png
LOGIN_CSS=/assets/sidra_realestate/css/berjaya-login.css

MODE=${1:-deploy}
APPDIR=$BENCH/apps/$APP

exec > >(tee -a "$LOG") 2>&1
echo "=== berjaya-deploy_v0.2.sh  $MODE  $(date -Is) ==="

say(){ echo; echo "==== $* ===="; }
die(){ echo; echo "STOPPED: $*"; echo "Nothing after this point was run. Log: $LOG"; exit 1; }

# Run a command in the bench folder as the frappe user (login shell, so bench/yarn are on PATH).
# Arguments are quoted one by one, so JSON and spaces pass through unchanged.
asfrappe(){ sudo -u "$FRAPPE_USER" -H bash -lc "cd $(printf %q "$BENCH") && $(printf '%q ' "$@")"; }
inapp(){ sudo -u "$FRAPPE_USER" -H bash -lc "cd $(printf %q "$APPDIR") && $(printf '%q ' "$@")"; }
# bench execute prints its return value as one line of JSON, after any warnings.
bexec(){ asfrappe bench --site "$SITE" execute "$@" 2>&1 | awk 'NF' | tail -1; }

RESULTS=()
pass(){ RESULTS+=("PASS          $*"); echo "PASS  $*"; }
fail(){ RESULTS+=("FAIL          $*"); echo "FAIL  $*"; }
unverified(){ RESULTS+=("NOT VERIFIED  $*"); echo "NOT VERIFIED  $*"; }

restart_bench(){
  if command -v supervisorctl >/dev/null 2>&1 && supervisorctl status >/dev/null 2>&1; then
    supervisorctl restart all || die "supervisor restart failed"
  elif asfrappe bench restart; then
    :
  else
    die "could not restart the bench processes. Restart them the way this server normally does, then run:
  bash $0 check"
  fi
  sleep 8
}

clear_caches(){
  asfrappe bench --site "$SITE" clear-cache || die "clear-cache failed"
  asfrappe bench --site "$SITE" clear-website-cache || die "clear-website-cache failed"
}

app_version(){ sed -n 's/^__version__ = "\(.*\)"/\1/p' "$APPDIR/$APP/__init__.py" 2>/dev/null; }

# ---------------------------------------------------------------------
preflight(){
  say "Preflight"
  [ "$(id -u)" -eq 0 ] || die "run as root"
  id "$FRAPPE_USER" >/dev/null 2>&1 || die "user $FRAPPE_USER does not exist"
  [ -d "$BENCH/sites/$SITE" ] || die "site folder $BENCH/sites/$SITE not found"
  [ -d "$APPDIR/.git" ] || die "$APPDIR is not a git checkout"
  asfrappe bench --version >/dev/null 2>&1 || die "bench does not run for user $FRAPPE_USER"
  echo "App version now: $(app_version)   commit: $(inapp git rev-parse --short HEAD)"

  local free_gb
  free_gb=$(df -BG --output=avail "$BENCH" | tail -1 | tr -dc '0-9')
  echo "Free disk: ${free_gb} GB"
  [ "${free_gb:-0}" -ge "$MIN_FREE_GB" ] || die "less than $MIN_FREE_GB GB free; the backup and build need room"

  # Lesson of 7 Nov: nginx must be able to read sites/assets through the home folders.
  local dir
  for dir in /home/$FRAPPE_USER "$(dirname "$BENCH")"; do
    if [ "$(( 0$(stat -c %a "$dir") & 05 ))" -ne 5 ]; then
      echo "Making $dir readable to nginx (was $(stat -c %a "$dir"))"
      chmod o+rx "$dir" || die "could not chmod $dir"
    fi
  done
}

# ---------------------------------------------------------------------
backup(){
  say "Backup with files (before any change)"
  local out rc
  out=$(asfrappe bench --site "$SITE" backup --with-files 2>&1); rc=$?
  echo "$out"
  { [ $rc -eq 0 ] && ! echo "$out" | grep -qi "traceback"; } || die "backup failed"
  # bench prints the files relative to sites/ ("./sidra.local/private/backups/..."): make them absolute.
  BACKUP_FILES=$(echo "$out" | grep -Eo '[^ ]*private/backups/[^ ]+' | sed "s|^\./|$BENCH/sites/|" | sort -u)
  [ -n "$BACKUP_FILES" ] || BACKUP_FILES="(see $BENCH/sites/$SITE/private/backups)"
  echo "BACKUP FILES:"; echo "$BACKUP_FILES"
}

# ---------------------------------------------------------------------
update_code(){
  say "Update $APP to $BRANCH (fast-forward only)"
  PREVIOUS=$(inapp git rev-parse HEAD)
  echo "Before: $PREVIOUS  $(inapp git status --short --branch | head -1)"
  echo "Stash list (read only, never applied or dropped):"
  inapp git stash list || true

  local dirty
  dirty=$(inapp git status --porcelain --untracked-files=no)
  [ -z "$dirty" ] || die "the app folder has uncommitted changes. Send these lines to the developer:
$dirty"

  REMOTE=$(inapp git remote -v | awk '/sidra-erp/ && /\(fetch\)/ {print $1; exit}')
  [ -n "$REMOTE" ] || die "no git remote points at sidra-erp. Remotes are:
$(inapp git remote -v)"

  # A rollback leaves the checkout detached: return to the branch first.
  if [ "$(inapp git rev-parse --abbrev-ref HEAD)" != "$BRANCH" ]; then
    inapp git checkout "$BRANCH" || die "could not switch back to $BRANCH"
  fi

  inapp git fetch "$REMOTE" "$BRANCH" || die "could not fetch $BRANCH from $REMOTE (network or GitHub access)"
  TARGET=$(inapp git rev-parse FETCH_HEAD)
  if [ "$(inapp git rev-parse HEAD)" = "$TARGET" ]; then
    echo "Already on the latest $BRANCH."
  else
    inapp git merge-base --is-ancestor HEAD "$TARGET" \
      || die "the server's code has commits that are not in $BRANCH, so it cannot be fast-forwarded"
    inapp git merge --ff-only "$TARGET" || die "fast-forward failed"
  fi
  echo "After:  $(inapp git rev-parse HEAD)   version $(app_version)"
  echo "Changes since the last deploy:"
  inapp git log --oneline --no-decorate "$PREVIOUS..HEAD" | head -30

  {
    echo "date=$(date -Is)"
    echo "previous_commit=$PREVIOUS"
    echo "deployed_commit=$(inapp git rev-parse HEAD)"
    echo "backup_files<<EOF"; echo "$BACKUP_FILES"; echo "EOF"
  } > "$STATE"
  echo "Rollback details saved to $STATE"
}

# ---------------------------------------------------------------------
build(){
  say "Install frontend packages and build"
  asfrappe node --version >/dev/null 2>&1 || die "node is not installed for $FRAPPE_USER"
  asfrappe yarn --version >/dev/null 2>&1 || die "yarn is not installed for $FRAPPE_USER"
  echo "node $(asfrappe node --version)   yarn $(asfrappe yarn --version)"
  # The app's root package.json installs frontend/ in its postinstall step.
  inapp yarn install --frozen-lockfile || die "yarn install failed (lockfile out of date or network)"
  # --force: build here rather than reuse cached assets, so the app's own build script runs
  # (it writes www/berjaya.html and public/berjaya/). The marker proves the files are new.
  local marker=/tmp/berjaya-build-start
  touch "$marker"
  asfrappe bench build --app "$APP" --force || die "bench build failed"
  [ -n "$(find "$APPDIR/$APP/www/berjaya.html" -newer "$marker" 2>/dev/null)" ] \
    || die "the build did not write a new $APP/www/berjaya.html"
  [ -n "$(find "$APPDIR/$APP/public/berjaya/assets" -name '*.js' -newer "$marker" 2>/dev/null | head -1)" ] \
    || die "the build wrote no new files to $APP/public/berjaya/assets"
  echo "Built: www/berjaya.html and $(ls "$APPDIR/$APP/public/berjaya/assets" | wc -l) asset files"
}

# ---------------------------------------------------------------------
migrate(){
  say "Migrate"
  local out rc
  out=$(asfrappe bench --site "$SITE" migrate 2>&1); rc=$?
  echo "$out" | tail -40
  { [ $rc -eq 0 ] && ! echo "$out" | grep -qi "traceback"; } || die "migrate failed. Read the lines above. The backup is listed in $STATE"
}

# ---------------------------------------------------------------------
http_code(){ curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASE_URL$1"; }

check(){
  say "Checks"
  local head target ver code body loc json

  # Code
  head=$(inapp git rev-parse HEAD)
  ver=$(app_version)
  REMOTE=${REMOTE:-$(inapp git remote -v | awk '/sidra-erp/ && /\(fetch\)/ {print $1; exit}')}
  if [ -n "$REMOTE" ] && inapp git fetch -q "$REMOTE" "$BRANCH" 2>/dev/null; then
    target=$(inapp git rev-parse FETCH_HEAD)
    if [ "$head" = "$target" ]; then pass "code is the latest $BRANCH (${head:0:7}, v$ver)"
    else fail "code ${head:0:7} (v$ver) is not the latest $BRANCH ${target:0:7}"; fi
  else
    unverified "code is the latest $BRANCH: could not fetch to compare (on ${head:0:7}, v$ver)"
  fi

  # Built files
  if [ -f "$APPDIR/$APP/www/berjaya.html" ] && ls "$APPDIR/$APP/public/berjaya/assets/"*.js >/dev/null 2>&1; then
    pass "Berjaya interface is built (www/berjaya.html and assets present)"
  else
    fail "Berjaya interface is not built: run this script in deploy mode"
  fi

  # Processes
  if command -v supervisorctl >/dev/null 2>&1 && supervisorctl status >/dev/null 2>&1; then
    local down
    down=$(supervisorctl status | grep -v RUNNING)
    if [ -z "$down" ]; then pass "all supervisor processes RUNNING"
    else fail "processes not running:
$down"; fi
  else
    unverified "process state: supervisor is not available to check"
  fi

  # Sign-in page
  code=$(http_code /login)
  body=$(curl -s --max-time 20 "$BASE_URL/login")
  if [ "$code" = 200 ]; then pass "/login answers 200"; else fail "/login answers $code"; fi
  if echo "$body" | grep -q "berjaya-login.css"; then pass "sign-in page loads the Berjaya stylesheet"
  else fail "sign-in page does not load berjaya-login.css (code not deployed, or caches not cleared)"; fi
  code=$(http_code "$LOGIN_CSS")
  if [ "$code" = 200 ]; then pass "stylesheet is served ($LOGIN_CSS)"
  else fail "stylesheet answers $code: nginx cannot read the assets (folder access) or bench build did not run"; fi
  if echo "$body" | grep -q "berjaya-wordmark.png"; then
    pass "sign-in page shows the Berjaya wordmark"
  else
    local wlogo nlogo
    wlogo=$(bexec frappe.db.get_single_value --args "['Website Settings', 'app_logo']")
    nlogo=$(bexec frappe.db.get_single_value --args "['Navbar Settings', 'app_logo']")
    fail "sign-in page logo is not the Berjaya wordmark. Settings hold: Website Settings app_logo=$wlogo, Navbar Settings app_logo=$nlogo. To set them to Berjaya: bash $0 brand"
  fi
  # Frappe v16's template renders "Sign In" and a logo, not app_name. Check
  # the settings actually used by login.get_context rather than grepping HTML.
  local website_name system_name
  website_name=$(bexec frappe.db.get_single_value --args "['Website Settings', 'app_name']")
  system_name=$(bexec frappe.db.get_single_value --args "['System Settings', 'app_name']")
  if python3 -c '
import json, sys
def value(text):
    # bench execute prints a string return value bare on this bench (Berjaya), or as JSON
    # ("Berjaya") on others; an empty line or "null" means not set.
    text = (text or "").strip()
    if text in ("", "null", "None"):
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text
website, system = (value(arg) for arg in sys.argv[1:])
sys.exit(0 if (website or system or "Frappe") == "Berjaya" else 1)
' "$website_name" "$system_name"; then
    pass "effective login app_name is Berjaya (Website Settings, falling back to System Settings)"
  else
    fail "login app_name could not be verified as Berjaya: Website Settings=$website_name, System Settings=$system_name. To apply branding: bash $0 brand"
  fi
  code=$(http_code "$LOGO")
  if [ "$code" = 200 ]; then pass "wordmark image is served"; else fail "wordmark image answers $code"; fi

  # /berjaya for a signed-out visitor: sent to the sign-in page, not shown, not an error
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASE_URL/berjaya/contracts")
  loc=$(curl -s -o /dev/null -w '%{redirect_url}' --max-time 20 "$BASE_URL/berjaya/contracts")
  if [[ "$code" =~ ^30[1278]$ ]] && [[ "$loc" == *"/login"* ]]; then
    pass "/berjaya/contracts sends a signed-out visitor to sign in ($code)"
  else
    fail "/berjaya/contracts for a signed-out visitor answered $code ${loc:+-> $loc} (expected a redirect to /login)"
  fi

  # The timeline API on a real contract (read only: it is a GET method that writes nothing).
  local before after
  before=$(bexec frappe.db.get_value --args "['Sidra Sale Contract', '$CONTRACT', 'modified']")
  json=$(asfrappe bench --site "$SITE" execute sidra_realestate.api.workflow.get_contract_timeline \
         --kwargs "{'contract': '$CONTRACT'}" 2>&1 | awk 'NF' | tail -1)
  after=$(bexec frappe.db.get_value --args "['Sidra Sale Contract', '$CONTRACT', 'modified']")
  if echo "$json" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d.get("stages"), list)' 2>/dev/null; then
    echo "$json" | python3 -m json.tool > "$TIMELINE_OUT"
    pass "timeline for $CONTRACT returned (saved to $TIMELINE_OUT)"
    echo "$json" | python3 -c '
import json, sys
d = json.load(sys.stdin)
t = d["transaction"]
print("    %s  %s  %s  supported=%s" % (t.get("name"), t.get("status"), t.get("source"), d.get("supported")))
for s in d["stages"]:
    mark = s["state"] + (" (skipped)" if s.get("skipped") else "") + (" (unavailable)" if s.get("unavailable") else "")
    print("    %-24s %-34s %s" % (s["key"], s["label"], mark))
'
    if [ "$before" = "$after" ]; then pass "timeline call changed nothing on $CONTRACT (modified unchanged)"
    else fail "$CONTRACT modified changed during the timeline call: $before -> $after"; fi
  else
    fail "timeline for $CONTRACT did not return stages. Output: $json"
  fi

  unverified "the screens in a signed-in browser: open $BASE_URL/berjaya/contracts/$CONTRACT and compare the panel with the stages above"
}

# ---------------------------------------------------------------------
brand(){
  say "Set the Berjaya logo and name on the sign-in page and navbar"
  echo "Before:"
  for pair in "Website Settings:app_logo" "Website Settings:favicon" "Website Settings:app_name" \
              "Navbar Settings:app_logo" "System Settings:app_name"; do
    echo "  $pair = $(bexec frappe.db.get_single_value --args "['${pair%%:*}', '${pair##*:}']")"
  done
  bexec frappe.db.set_single_value --args "['Website Settings', 'app_logo', '$LOGO']" >/dev/null || die "could not set Website Settings app_logo"
  bexec frappe.db.set_single_value --args "['Website Settings', 'favicon', '$FAVICON']" >/dev/null || die "could not set Website Settings favicon"
  bexec frappe.db.set_single_value --args "['Website Settings', 'app_name', 'Berjaya']" >/dev/null || die "could not set Website Settings app_name"
  bexec frappe.db.set_single_value --args "['Navbar Settings', 'app_logo', '$LOGO']" >/dev/null || die "could not set Navbar Settings app_logo"
  bexec frappe.db.set_single_value --args "['System Settings', 'app_name', 'Berjaya']" >/dev/null || die "could not set System Settings app_name"
  echo "After:"
  for pair in "Website Settings:app_logo" "Navbar Settings:app_logo" "Website Settings:app_name"; do
    echo "  $pair = $(bexec frappe.db.get_single_value --args "['${pair%%:*}', '${pair##*:}']")"
  done
  clear_caches
}

# ---------------------------------------------------------------------
rollback(){
  local commit=${1:-}
  [ -n "$commit" ] || die "give the commit to return to, e.g.: bash $0 rollback <commit>  (see previous_commit in $STATE)"
  say "Roll the code back to $commit"
  inapp git cat-file -e "$commit^{commit}" 2>/dev/null || die "commit $commit is not in the server's checkout"
  local dirty
  dirty=$(inapp git status --porcelain --untracked-files=no)
  [ -z "$dirty" ] || die "the app folder has uncommitted changes:
$dirty"
  read -r -p "Type ROLLBACK to move the code from $(inapp git rev-parse --short HEAD) to $commit: " answer
  [ "$answer" = "ROLLBACK" ] || die "not confirmed"
  backup
  inapp git checkout --detach "$commit" || die "checkout failed"
  build
  migrate
  clear_caches
  restart_bench
  echo
  echo "Code is now at $(inapp git rev-parse --short HEAD) (detached). The next deploy returns it to $BRANCH."
  echo "The DATABASE WAS NOT RESTORED. Only if a migration changed data, restore the backup taken"
  echo "before the deploy, after reading it carefully (it replaces the whole site's data):"
  echo "  cd $BENCH && sudo -u $FRAPPE_USER bench --site $SITE restore <database .sql.gz> \\"
  echo "       --with-public-files <files .tar> --with-private-files <private-files .tar>"
  echo "Backup files of the last deploy:"
  sed -n '/^backup_files<<EOF/,/^EOF/p' "$STATE" 2>/dev/null | sed '1d;$d'
}

# ---------------------------------------------------------------------
summary(){
  say "Summary"
  printf '%s\n' "${RESULTS[@]}"
  local failed
  failed=$(printf '%s\n' "${RESULTS[@]}" | grep -c '^FAIL' || true)
  echo
  if [ "$failed" -eq 0 ]; then
    echo "No check failed. Sign in at $BASE_URL/login, then open $BASE_URL/berjaya"
  else
    echo "$failed check(s) failed. Send this summary as it is."
  fi
  echo "Log: $LOG"
  [ "$failed" -eq 0 ]
}

case "$MODE" in
  deploy)
    preflight
    backup
    update_code
    build
    migrate
    say "Clear caches and restart"
    clear_caches
    restart_bench
    check
    summary
    ;;
  check)
    preflight
    check
    summary
    ;;
  brand)
    preflight
    brand
    check
    summary
    ;;
  rollback)
    preflight
    rollback "${2:-}"
    ;;
  *)
    die "unknown mode '$MODE'. Use: deploy | check | brand | rollback <commit>"
    ;;
esac
