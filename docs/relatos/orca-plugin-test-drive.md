# Draft report to Orca: `orca plugin test` fails when the plugin is on another drive

Draft only. Not sent anywhere; the maintainer files it.

## Orca version

1.4.257 when first seen; 1.4.258 is installed now.

## OS

Windows 11 Pro.

## Steps to reproduce

1. Install Orca on drive C:.
2. Check out a repository containing an Orca plugin on drive F:.
3. From the plugin folder on F:, run `orca plugin test` (or `orca plugin check`).

## Expected

The harness runs the plugin tests regardless of which drive holds the plugin.

## Actual

The harness stops with `orca-testing.mjs: cannot import "./orca-runtime.mjs"`. It does not find `orca-runtime.mjs` when the plugin and the Orca installation are on different drives.

## Workaround

Create a git worktree of the same tree on the drive where Orca is installed (C:) and run `orca plugin test` / `orca plugin check` from there. The same tree passed in a worktree on C:.
