#!/usr/bin/env node
/**
 * Chief-first coordination reminder for telegram-medical-channels.
 * Fires on sessionStart, subagentStop, and stop (see .cursor/hooks.json).
 *
 * Within Cursor only - not a 24/7 OS daemon. Fail-open on errors (exit 0, {}).
 * Dedupes via .cursor/chief-session-state.json (gitignored).
 */
import { execFileSync } from "node:child_process";
import { readFileSync, readSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = process.cwd();
const STATE_PATH = join(repoRoot, ".cursor", "chief-session-state.json");
const EXEC_TIMEOUT_MS = 2500;
const EXEC_MAX_BUFFER = 1024 * 1024;
const DEDUPE_MINUTES = 5;
const DEFAULT_REPO = "yanniedog/telegram-medical-channels";

function run(command, args = []) {
  try {
    return execFileSync(command, args, {
      windowsHide: true,
      cwd: repoRoot,
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: EXEC_TIMEOUT_MS,
      maxBuffer: EXEC_MAX_BUFFER,
    }).trim();
  } catch (error) {
    if (error && (error.code === "ETIMEDOUT" || error.signal === "SIGTERM")) {
      return "";
    }
    throw error;
  }
}


function readStdinHookEvent() {
  try {
    if (process.stdin.isTTY) return "";
    const buf = Buffer.alloc(65536);
    let n = 0;
    try {
      n = readSync(0, buf, 0, buf.length, null);
    } catch {
      return "";
    }
    if (!n) return "";
    const raw = buf.slice(0, n).toString("utf8").trim();
    if (!raw) return "";
    const parsed = JSON.parse(raw);
    return typeof parsed?.hook_event_name === "string" ? parsed.hook_event_name : "";
  } catch {
    return "";
  }
}

function readState() {
  try {
    const raw = readFileSync(STATE_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function writeState(patch) {
  try {
    mkdirSync(dirname(STATE_PATH), { recursive: true });
    const next = { ...readState(), ...patch };
    writeFileSync(STATE_PATH, `${JSON.stringify(next, null, 2)}\n`, "utf8");
  } catch {}
}

export function recentlyCompleted(state, now = Date.now()) {
  const at = state.lastChiefCompletedAt;
  if (!at) return false;
  const ms = now - Date.parse(at);
  return Number.isFinite(ms) && ms >= 0 && ms < DEDUPE_MINUTES * 60 * 1000;
}

function countAgentBranches() {
  try {
    const branches = run("git", ["branch", "--list", "agent/*"]);
    if (!branches) return 0;
    return branches.split(/\r?\n/).filter(Boolean).length;
  } catch {
    return 0;
  }
}

function buildMessage({ hookEvent, dirty, openPrCount, agentBranchCount }) {
  const needsShipBar = dirty || openPrCount > 0;
  const signals = [];
  if (dirty) signals.push("uncommitted changes");
  if (openPrCount > 0) signals.push(`${openPrCount} open PR(s)`);
  if (agentBranchCount > 1) signals.push(`${agentBranchCount} agent/* branches`);

  const scanLine =
    "Mandatory cycle: SCAN -> LOCK CHECK -> PLAN -> DELEGATE orchestrator (ship bar only when chief assigns).";
  const spawnLine =
    "Spawn chief NOW: Task subagent_type=generalPurpose, run_in_background=true, prompt follows .cursor/skills/chief-agent/SKILL.md - one full coordination cycle before any feature edits, commits, or new domain work.";

  if (hookEvent === "sessionStart") {
    if (needsShipBar) {
      return (
        `Chief agent (session start): ${signals.join("; ")}. ` +
        `${scanLine} ${spawnLine} Partition uncommitted work into one PR per task on agent/<slug>; never commit directly to main.`
      );
    }
    return (
      `Chief agent (session start): repo looks clean (no dirty tree / open PRs). ` +
      `${scanLine} ${spawnLine} Parent agents must not skip chief; chief delegates git/PR to workflow-orchestrator.`
    );
  }

  if (needsShipBar) {
    return (
      `Chief agent: ${signals.join(" and ")} after ${hookEvent || "agent stop"}. ` +
      `${scanLine} ${spawnLine} Do not bundle unrelated discovery/scrape/registry/workbook changes in one PR.`
    );
  }

  return (
    `Chief agent: run post-subagent coordination (${hookEvent || "stop"}). ` +
    `${scanLine} ${spawnLine}`
  );
}

function githubRepoSlug() {
  try {
    const url = run("git", ["config", "--get", "remote.origin.url"]);
    const match = url.match(/github\.com[:/]([^/]+\/[^/.]+)/);
    return match ? match[1].replace(/\.git$/, "") : DEFAULT_REPO;
  } catch {
    return DEFAULT_REPO;
  }
}

function main() {
  const hookEvent = readStdinHookEvent();

  if (hookEvent !== "sessionStart" && recentlyCompleted(readState())) {
    console.log("{}");
    return;
  }

  let dirty = false;
  let openPrCount = 0;
  let agentBranchCount = 0;

  try {
    dirty = Boolean(run("git", ["status", "--porcelain"]));
  } catch {}

  try {
    const slug = githubRepoSlug();
    const out = run("gh", ["pr", "list", "--state", "open", "--json", "number", "--repo", slug]);
    const parsed = JSON.parse(out || "[]");
    openPrCount = Array.isArray(parsed) ? parsed.length : 0;
  } catch {}

  agentBranchCount = countAgentBranches();

  const needsStrongChief = dirty || openPrCount > 0;
  const alwaysChief =
    hookEvent === "sessionStart" ||
    hookEvent === "subagentStop" ||
    hookEvent === "stop";

  if (!alwaysChief && !needsStrongChief && agentBranchCount <= 1) {
    console.log("{}");
    return;
  }

  const msg = buildMessage({ hookEvent, dirty, openPrCount, agentBranchCount });

  writeState({
    lastChiefReminderAt: new Date().toISOString(),
    lastHookEvent: hookEvent || "unknown",
  });
  console.log(JSON.stringify({ followup_message: msg }));
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  try { main(); } catch { console.log("{}"); }
}
