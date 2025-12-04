from nodupe.utils.ffmpeg_progress import _parse_time_string, _parse_ffmpeg_duration_from_cmd  # noqa: E501


def test_parse_time_string_seconds():
    assert _parse_time_string('5') == 5.0
    assert _parse_time_string('1.5') == 1.5


def test_parse_time_string_hms():
    assert _parse_time_string('00:00:05') == 5.0
    assert _parse_time_string('00:01:30') == 90.0
    assert _parse_time_string('1:00:00') == 3600.0


def test_parse_duration_from_cmd_t_and_to():
    assert _parse_ffmpeg_duration_from_cmd(['ffmpeg', '-t', '10']) == 10.0
    assert _parse_ffmpeg_duration_from_cmd(['ffmpeg', '-to', '12']) == 12.0
    assert _parse_ffmpeg_duration_from_cmd(
        ['ffmpeg', '-ss', '5', '-to', '8']) == 3.0
    # combined forms
    assert _parse_ffmpeg_duration_from_cmd(['ffmpeg', '-t3.5']) == 3.5
    assert _parse_ffmpeg_duration_from_cmd(
        ['ffmpeg', '-ss00:00:05', '-to00:00:10']) == 5.0
    # combination -ss + -t should use -t as the segment length
    assert _parse_ffmpeg_duration_from_cmd(
        ['ffmpeg', '-ss', '5', '-t', '3']) == 3.0
