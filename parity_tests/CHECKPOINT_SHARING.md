# Windows State Sweep checkpoint replacement

Status: Unreleased. Recorded: 2026-09-20.

`StateSweepCheckpoint.H` contains the publisher used by the solver and the
small `checkpoint_sharing` CMake probe. Existing checkpoints use `ReplaceFileA`,
which can replace a destination held by deletion-sharing readers. First
publication uses `MoveFileExA` without REPLACE_EXISTING; a racing destination
therefore returns to the replacement path on the next retry. Forty 50-ms
attempts remain. Failure reports the saved Windows error and retained temporary
path. No delete-then-write window or in-place truncation is introduced.

Deploy with the VDS checkpoint reader using CreateFileW with READ/WRITE/DELETE
sharing. Changing only the reader is insufficient with the old MoveFileEx
publisher; changing only the writer leaves ordinary readers able to block it.
Checkpoints keep their existing hash/next-row/total format and resume semantics.
External incompatible locks or actual denied permissions still fail explicitly.

The paired change was tested with the complete rebuilt solver on two copied
Foil04 native states, holding its initial checkpoint open across the entire
14.635-second solve. Both rows published; the old handle retained the old
record while new opens saw the final one. All nine compared CF/CM/CD/CL/CS
coefficients exactly matched the installed baseline (tolerance 1e-9).
This is I/O and regression validation, not new physical aerodynamic validation.
An incompatible ordinary reader was also held open against the full solver:
it failed explicitly after retries, retaining old row 0 and temporary row 1.

The standalone probe compiled, but Windows application control blocked its
launch with error 4551. No policy was disabled. The full solver could launch
and supplied the native contention validation instead. Parent VDS tests also
cover 500 replacements while readers hold each previous record open, invalid
records, resume, queues and persistence. See the parent checkpoint review for
test totals and deployment status.

References: [Microsoft ReplaceFile](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)
documents sharing and failure semantics; [LLVM's corresponding Windows fix](https://reviews.llvm.org/D13647)
describes why a retry loop around MoveFileEx alone is insufficient.
