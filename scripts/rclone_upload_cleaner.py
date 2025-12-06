#!/usr/bin/env python3
"""
rclone_upload_cleaner.py

Find rclone mounts, locate an Upload folder, list top-level subfolders and
provide a safe dry-run and optional destructive purge.

Usage: run the script and follow the interactive prompts.

This script is intentionally conservative: dry-run is the default and the
actual deletion requires typing a confirmation phrase.
"""

import os
import re
import shlex
import subprocess
import sys
from typing import List, Tuple, Optional


def parse_proc_mounts() -> List[Tuple[str, str, str]]:
    """Return a list of (source, target, fstype) from /proc/mounts"""
    mounts = []
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3:
                    source, target, fstype = parts[0], parts[1], parts[2]
                    mounts.append((source, target, fstype))
    except Exception:
        pass
    return mounts


def find_rclone_mounts() -> List[Tuple[str, str, str]]:
    """Find mount entries that look like rclone mounts.

    Returns list of (source, target, fstype)."""
    result = []
    proc = parse_proc_mounts()
    for source, target, fstype in proc:
        # fstype on rclone mounts usually contains 'fuse.rclone'
        if 'fuse.rclone' in fstype.lower() or 'rclone' in fstype.lower():
            result.append((source, target, fstype))
        # Some setups show the source like 'gdrive:' with fstype 'fuse'
        elif source and ':' in source and 'fuse' in fstype.lower():
            # Heuristic: if source looks like remote: and target exists, treat it
            result.append((source, target, fstype))
    return result


def ps_for_rclone_mounts() -> List[Tuple[str, str]]:
    """Look for running 'rclone mount' processes and return tuples of (remote_source, mount_target)

    This is a best-effort parser of the commandline output.
    """
    res = []
    try:
        out = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=False)
        for line in out.stdout.splitlines():
            if 'rclone mount' in line and 'grep' not in line:
                # commandline contains words 'rclone mount REVISIT'
                parts = shlex.split(line)
                # fallback: try to find 'rclone' and 'mount' and next args
                # ps aux output has lots of columns; safe heuristic: whole line for path
                # We'll try to parse the command after the 10th field
                # Simpler: split at ' rclone mount ' and parse remainder
                try:
                    cmd = line.split('rclone mount', 1)[1].strip()
                    # cmd typically looks like: 'remote: /path/to/mount --opt'
                    p = shlex.split(cmd)
                    if len(p) >= 2 and ':' in p[0]:
                        res.append((p[0], p[1]))
                    elif len(p) >= 1 and ':' in p[-1]:
                        res.append((p[0], p[-1]))
                except Exception:
                    continue
    except Exception:
        pass
    return res


def list_subdirs_on_target(target_path: str) -> List[str]:
    try:
        upath = os.path.join(target_path, 'Upload')
        if os.path.isdir(upath):
            entries = os.listdir(upath)
            subdirs = [e for e in entries if os.path.isdir(os.path.join(upath, e))]
            return subdirs
    except Exception:
        pass
    return []


def list_subdirs_for_remote(remote: str) -> Optional[List[str]]:
    """Use rclone lsf --dirs-only remote:Upload to list top-level folders if possible."""
    try:
        out = subprocess.run(['rclone', 'lsf', '--dirs-only', f'{remote}Upload'], text=True, capture_output=True, check=False)
        if out.returncode == 0:
            # rclone lsf prints names, often with trailing / for dirs
            lines = [l.strip().rstrip('/') for l in out.stdout.splitlines() if l.strip()]
            return lines
        else:
            # If the path isn't available, try 'remote:Upload' (with colon)
            if not remote.endswith(':'):
                out2 = subprocess.run(['rclone', 'lsf', '--dirs-only', f'{remote}:Upload'], text=True, capture_output=True, check=False)
                if out2.returncode == 0:
                    return [l.strip().rstrip('/') for l in out2.stdout.splitlines() if l.strip()]
    except FileNotFoundError:
        print('rclone executable not found in PATH. Install rclone or run script where rclone is available.')
    except Exception:
        pass
    return None


def confirm(prompt: str) -> bool:
    try:
        r = input(prompt + ' [y/N] ')
    except KeyboardInterrupt:
        print()
        return False
    return r.lower().strip() in ('y', 'yes')


def main():
    print('\nrclone_upload_cleaner - conservative helper to remove subfolders under Upload')
    print('This will PRESERVE the Upload folder itself and any files at the Upload root.')

    mounts = find_rclone_mounts()
    process_mounts = ps_for_rclone_mounts()

    candidates = []  # tuples (source, target, fstype)

    if mounts:
        for src, tgt, fstype in mounts:
            upath = os.path.join(tgt, 'Upload')
            if os.path.isdir(upath):
                candidates.append((src, tgt, fstype))

    # Add ps-found mounts which might have Upload if not already included
    for src, tgt in process_mounts:
        if not any(tgt == c[1] for c in candidates):
            upath = os.path.join(tgt, 'Upload')
            if os.path.isdir(upath):
                candidates.append((src, tgt, 'ps-found'))

    if not candidates:
        print('\nNo rclone-mounted Upload folder found automatically.')
        print('Options:')
        print('  1) Provide an rclone remote name (e.g. gdrive:) to probe remote:Upload')
        print('  2) Provide a local path to an existing mount that contains Upload')
        print('  3) Exit')
        choice = input('Choose (1/2/3) [3]: ').strip() or '3'
        if choice == '3':
            print('No action taken. Exiting.')
            return
        if choice == '1':
            remote = input('Enter rclone remote name (include trailing colon if you use it in your configs, e.g. gdrive:): ').strip()
            # Normalize remote to include trailing colon
            if not remote.endswith(':'):
                remote = remote + ':'
            print(f'Probing remote {remote}Upload')
            subdirs = list_subdirs_for_remote(remote)
            if subdirs is None:
                print('Could not list remote: ensure rclone is installed and your remote name is correct.')
                return
            if not subdirs:
                print('No subfolders found under remote Upload or Upload does not exist.')
                return
            print('\nTop-level folders under remote Upload:')
            for s in subdirs:
                print('  -', s)

            # Show dry-run rclone purge commands for each
            print('\nDRY-RUN commands (these will not delete anything):')
            for s in subdirs:
                print('    rclone purge --dry-run', f'"{remote}Upload/{s}"')

            if confirm('Run the dry-run now (recommended) ?'):
                for s in subdirs:
                    print('\n--- DRY-RUN:', f'{remote}Upload/{s}')
                    subprocess.run(['rclone', 'purge', '--dry-run', f'{remote}Upload/{s}'])

            if confirm('Proceed to actually delete ALL these subfolders (this is destructive)? Type YES to proceed'):
                yn = input('Type EXACTLY THIS to confirm: DELETE ALL SUBFOLDERS -> ') or ''
                if yn.strip() == 'DELETE ALL SUBFOLDERS ->':
                    for s in subdirs:
                        print('\nPurging', f'{remote}Upload/{s}')
                        subprocess.run(['rclone', 'purge', f'{remote}Upload/{s}'])
                    print('\nDone.')
                else:
                    print('Confirmation mismatch — aborting.')
            else:
                print('Skipped actual deletion.')
            return

        if choice == '2':
            local = input('Enter local path that contains Upload (eg /mnt/gdrive): ').strip()
            upath = os.path.join(local, 'Upload')
            if not os.path.isdir(upath):
                print('Upload not found under that path: ', upath)
                return
            subdirs = [d for d in os.listdir(upath) if os.path.isdir(os.path.join(upath, d))]
            if not subdirs:
                print('No subfolders found under', upath)
                return
            print('\nFound the following top-level subfolders:')
            for s in subdirs:
                print('  -', s)
            print('\nDRY-RUN will show rm -rf commands (local file deletion, read-only dry-run).')
            for s in subdirs:
                print('    DRY -> rm -rf', os.path.join(upath, s))
            if confirm('Run a safe dry-run check (verify accessibility)?'):
                for s in subdirs:
                    print('\nListing contents (first 20 entries) of', os.path.join(upath, s))
                    try:
                        entries = os.listdir(os.path.join(upath, s))[:20]
                        for e in entries:
                            print('  ', e)
                    except Exception as exc:
                        print('  error listing:', exc)
            if confirm('Proceed to actually delete all these subfolders under Upload (this will delete them from the mounted drive)?'):
                # Need one more exact confirmation
                yn = input('Type EXACTLY: DELETE ALL SUBFOLDERS -> ') or ''
                if yn.strip() == 'DELETE ALL SUBFOLDERS ->':
                    for s in subdirs:
                        path = os.path.join(upath, s)
                        print('\nRemoving', path)
                        # Use os.rmdir or shutil.rmtree
                        try:
                            import shutil
                            shutil.rmtree(path)
                        except Exception as exc:
                            print('  failed to remove', path, 'error:', exc)
                    print('\nDone.')
                else:
                    print('Confirmation mismatch — aborting.')
            else:
                print('Skipped actual deletion.')
            return

    # If we reached here and have candidates
    print('\nDetected rclone mounts with an Upload folder:')
    for idx, (src, tgt, fstype) in enumerate(candidates, start=1):
        print(f'{idx}) source={src} target={tgt} fstype={fstype}')

    pick = input('\nChoose a mount number to operate on (or q to quit) [1]: ').strip() or '1'
    if pick.lower() in ('q', 'quit'):
        print('Quitting — no action taken.')
        return
    try:
        i = int(pick) - 1
    except Exception:
        print('Invalid choice.')
        return

    src, tgt, fstype = candidates[i]
    print('\nOperating on:')
    print(' - source:', src)
    print(' - target:', tgt)
    upath = os.path.join(tgt, 'Upload')

    subdirs = list_subdirs_on_target(tgt)

    if subdirs:
        print('\nTop-level subfolders under', upath, ':')
        for s in subdirs:
            print('  -', s)
    else:
        print('\nNo subfolders found in', upath)
        # Try the remote-based listing as a fallback if source looks like remote:
        if ':' in src:
            # normalize remote name
            rname = src if src.endswith(':') else (src + ':')
            print('Trying rclone listing for remote', rname)
            remote_subs = list_subdirs_for_remote(rname)
            if remote_subs:
                subdirs = remote_subs
                print('\nTop-level folders under remote', rname + 'Upload:')
                for s in subdirs:
                    print('  -', s)

    if not subdirs:
        print('Nothing to delete. Exiting.')
        return

    # Present clean dry-run commands (prefer remote-based if source contains a remote name)
    remote_hint = None
    if ':' in src:
        rname = src if src.endswith(':') else (src + ':')
        remote_hint = rname

    print('\nDRY-RUN commands (these will not delete anything):')
    if remote_hint:
        for s in subdirs:
            print('   rclone purge --dry-run', f'"{remote_hint}Upload/{s}"')
    else:
        for s in subdirs:
            print('   DRY -> listing first files for', os.path.join(upath, s))

    if confirm('\nRun the dry-run commands now?'):
        if remote_hint:
            for s in subdirs:
                print('\n--- DRY-RUN', f'{remote_hint}Upload/{s}')
                subprocess.run(['rclone', 'purge', '--dry-run', f'{remote_hint}Upload/{s}'])
        else:
            for s in subdirs:
                print('\nListing', os.path.join(upath, s))
                try:
                    entries = os.listdir(os.path.join(upath, s))[:20]
                    for e in entries:
                        print('   ', e)
                except Exception as exc:
                    print('   error listing:', exc)

    if confirm('\nProceed to actually delete ALL these subfolders (this is destructive)?'):
        print('\nExtra confirmation required: type EXACTLY: DELETE ALL SUBFOLDERS ->')
        yn = input('> ')
        if yn.strip() != 'DELETE ALL SUBFOLDERS ->':
            print('Confirmation did not match. Aborting.')
            return

        # Perform the destructive action
        if remote_hint:
            for s in subdirs:
                print('\nPurging', f'{remote_hint}Upload/{s}')
                subprocess.run(['rclone', 'purge', f'{remote_hint}Upload/{s}'])
        else:
            for s in subdirs:
                path = os.path.join(upath, s)
                print('\nRemoving local path', path)
                try:
                    import shutil
                    shutil.rmtree(path)
                except Exception as exc:
                    print('  failed to remove', path, 'error:', exc)

        print('\nAll selected subfolders removed.')
    else:
        print('Skipped actual deletion. Nothing changed.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted - exiting')
        sys.exit(1)
