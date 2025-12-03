import os
import subprocess
import sys


def _parse_time_string(value: str) -> float | None:
    """Parse an ffmpeg time string (seconds or HH:MM:SS[.ms]) into seconds.

    Returns a float or None if parsing failed.
    """
    if value is None:
        return None
    value = str(value).strip()
    if value == '':
        return None
    # pure numeric
    try:
        return float(value)
    except Exception:
        pass

    # HH:MM:SS[.xxx]
    parts = value.split(':')
    try:
        parts = [float(p) for p in parts]
        # Support s, m:s, h:m:s
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return parts[0] * 60.0 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600.0 + parts[1] * 60.0 + parts[2]
    except Exception:
        return None


def _parse_ffmpeg_duration_from_cmd(cmd: list) -> float | None:
    """Parse common ffmpeg args (-t, -to, -ss) to infer expected duration.

    Logic:
    - If both -ss and -to present -> duration = to - ss
    - Else if -t present -> duration = t
    - Else if -to present -> duration = to
    - Returns None when not inferable.
    """
    ss = None
    to = None
    t = None

    i = 0
    while i < len(cmd):
        a = cmd[i]
        if a == '-ss' and i + 1 < len(cmd):
            ss = _parse_time_string(cmd[i + 1])
            i += 2
            continue
        if a.startswith('-ss') and len(a) > 3:  # -ssVALUE
            ss = _parse_time_string(a[3:])
            i += 1
            continue

        if a == '-to' and i + 1 < len(cmd):
            to = _parse_time_string(cmd[i + 1])
            i += 2
            continue
        if a.startswith('-to') and len(a) > 3:
            to = _parse_time_string(a[3:])
            i += 1
            continue

        if a == '-t' and i + 1 < len(cmd):
            t = _parse_time_string(cmd[i + 1])
            i += 2
            continue
        if a.startswith('-t') and len(a) > 2:
            t = _parse_time_string(a[2:])
            i += 1
            continue

        i += 1

    if ss is not None and to is not None:
        try:
            dur = float(to - ss)
            return max(0.0, dur)
        except Exception:
            pass

    if t is not None:
        return max(0.0, float(t))

    if to is not None:
        return max(0.0, float(to))

    return None


def run_ffmpeg_with_progress(
    cmd, expected_duration: float | None = None, max_wait=12,
    timeout: float | None = None, force_mode: str | None = None,
    probe_input_duration: bool = True, show_eta: bool = True
):
    """Run an ffmpeg command with an interactive (or CI-safe) progress helper.

    See tests for usage. This helper will try to infer duration from -t/-to/-ss
    and will fallback to probing the input file if ffprobe is available.
    """
    # Try to infer duration from command args first (-t / -to / -ss)
    if expected_duration is None:
        expected_duration = _parse_ffmpeg_duration_from_cmd(cmd)

    # Probe inputs with ffprobe when still unknown
    if expected_duration is None and probe_input_duration:
        for a in cmd:
            if isinstance(a, str) and os.path.exists(a) and os.path.isfile(a):
                try:
                    res = subprocess.run([
                        'ffprobe', '-v', 'error', '-show_entries',
                        'format=duration', '-of',
                        'default=noprint_wrappers=1:nokey=1', a
                    ], capture_output=True, text=True, check=True)
                    out = res.stdout.strip()
                    if out:
                        expected_duration = max(
                            0.1, float(out.splitlines()[0])
                        )
                        break
                except Exception:
                    # ignore probe failure and fall back
                    pass

    if expected_duration is None:
        expected_duration = 1.0

    try:
        # Capture stderr so we can report it on failure to help debugging in CI
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
        )
    except FileNotFoundError:
        return False

    print('\n[TEST NOTICE] Running ffmpeg (ETA estimated). Please wait...')
    start = __import__('time').time()
    spinner = ['|', '/', '-', '\\']
    spin_i = 0

    env_mode = os.environ.get('NO_DUPE_PROGRESS', '').lower() or None
    if force_mode is None:
        mode = env_mode or 'auto'
    else:
        mode = force_mode

    interactive = sys.stdout.isatty()
    if mode == 'quiet':
        interactive = False
    elif mode == 'interactive':
        interactive = True

    prev_len = 0
    last_print_time = 0.0
    last_filled = -1
    update_count = 0
    max_updates = 6

    try:
        if interactive:
            while proc.poll() is None:
                now = __import__('time').time()
                elapsed = now - start
                remaining = max(0.0, expected_duration - elapsed)
                percent = min(
                    100.0, (elapsed / expected_duration) * 100.0
                ) if expected_duration > 0 else 0.0
                bar_len = 30
                filled = int(
                    bar_len * min(1.0, elapsed / expected_duration)
                ) if expected_duration > 0 else 0
                bar = (
                    '[' + '=' * filled + '>' +
                    ' ' * max(0, bar_len - filled - 1) + ']'
                )
                spinner_ch = spinner[spin_i % len(spinner)]
                eta_str = f"ETA: {remaining:.1f}s" if show_eta else ''
                msg = (
                    f"[TEST PROGRESS] {spinner_ch} {bar} {percent:5.1f}%  "
                    f"{eta_str}  elapsed: {elapsed:.1f}s"
                )

                pad = ''
                if prev_len > len(msg):
                    pad = ' ' * (prev_len - len(msg))

                now_print = __import__('time').time()
                if (
                    (filled != last_filled or
                     (now_print - last_print_time) >= 0.5) and
                    update_count < max_updates
                ):
                    sys.stdout.write('\r' + msg + pad)
                    sys.stdout.flush()
                    last_print_time = now_print
                    last_filled = filled
                    update_count += 1

                prev_len = max(prev_len, len(msg))
                spin_i += 1
                __import__('time').sleep(0.18)

                # If a hard timeout is set, terminate the process and fail.
                if timeout is not None and elapsed > timeout:
                    sys.stdout.write(
                        '\n[TEST ERROR] ffmpeg exceeded timeout — '
                        'killing process\n'
                    )
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return False

                # Otherwise, if we've exceeded the soft max_wait threshold,
                # warn and stop showing interactive progress updates (but
                # continue to wait for ffmpeg).
                if elapsed > max_wait:
                    sys.stdout.write(
                        '\n[TEST WARNING] ffmpeg build exceeded max wait — '
                        'continuing\n'
                    )
                    break
        else:
            while proc.poll() is None:
                # Enforce a timeout while waiting in non-interactive mode as
                # well.
                if timeout is not None:
                    now = __import__('time').time()
                    if (now - start) > timeout:
                        sys.stderr.write(
                            '\n[TEST ERROR] ffmpeg exceeded timeout — '
                            'killing process\n'
                        )
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        return False

                    __import__('time').sleep(0.2)

        end = __import__('time').time()
        elapsed = end - start
        bar_len = 30
        eta_label = 'ETA: 0.0s' if show_eta else ''
        final_msg = (
            f"[TEST PROGRESS] [{'=' * bar_len}] 100.0%  {eta_label}  "
            f"elapsed: {elapsed:.1f}s"
        )
        pad = ''
        if prev_len > len(final_msg):
            pad = ' ' * (prev_len - len(final_msg))
        if interactive:
            sys.stdout.write('\r' + final_msg + pad + '\n')
        else:
            sys.stdout.write(final_msg + '\n')
        sys.stdout.flush()

        # If ffmpeg failed, capture stderr and show a short helpful snippet
        if proc.returncode != 0:
            try:
                _, stderr = proc.communicate(timeout=0.5)
            except Exception:
                stderr = None

            # Show a concise diagnostic — limit to first 5 lines
            if stderr:
                lines = [line for line in stderr.splitlines() if line.strip()]
                snippet = '\n'.join(lines[:5])
                sys.stderr.write(
                    f"[TEST ERROR] ffmpeg failed (rc={proc.returncode}). "
                    f"Stderr:\n{snippet}\n"
                )
            else:
                sys.stderr.write(
                    f"[TEST ERROR] ffmpeg failed (rc={proc.returncode}), "
                    "no stderr captured.\n"
                )

            return False

        return True
    except KeyboardInterrupt:
        try:
            proc.kill()
        except Exception:
            pass
        raise
