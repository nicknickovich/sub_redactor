import argparse
import datetime as dt
import os
import re


MIN_TIME = dt.timedelta(0)
ASS_REGEX = re.compile(
    r"""(Dialogue:\s\d,)
    (\d:\d\d:\d\d\.\d\d),
    (\d:\d\d:\d\d\.\d\d),
    (.*)""", re.X)

parser = argparse.ArgumentParser(
    description="""Shift subtitle timings in batch and other manipulations
                   with subtitle files. Only supports .srt and .ass subtitles"""
)
parser.add_argument(
    "-f", "--first", action="store_true",
    help="Print out the time of the first line in seconds."
)
parser.add_argument(
    "-s", "--seconds", type=int, default=0,
    help="Shift all lines by given amount of seconds."
)
parser.add_argument(
    "-m", "--millisec", type=int, default=0,
    help="Shift all lines by given amount of milliseconds."
)
parser.add_argument(
    "--f-min", action="store_true",
    help="""Print out the minimum time of the first line in seconds among
            selected files. Among all files if none selected."""
)
parser.add_argument(
    "-l", "--line", type=int, default=0,
    help="""Shift all lines starting from provided line number in the file.
            First line has number 1."""
)
parser.add_argument(
    "-n", "--file-number", type=int, nargs="+",
    help="""Ordinal number of subtitle files that will be modified.
            Has no connection to the number in filename. Only subtitle files 
            are counted.
            First file has number 1."""
)
parser.add_argument(
    "-c", "--no-confirm", action="store_true", dest="no_confirm",
    help="Proceed without confirmation."
)

args = parser.parse_args()

confirmation = args.no_confirm

if args.millisec or args.seconds:
    if not confirmation:
        answer = input("Are you sure? [Yes/No]\n") or "Yes"
    while not confirmation:
        if answer in ("Yes", "yes", "Y", "y"):
            confirmation = True
        elif answer in ("No", "no", "N", "n"):
            parser.exit()
        else:
            answer = input("Type Yes or No\n")


def timestr_to_timedelta(timestr, extension):
    if extension == "srt":
        m = re.match(r"(\d\d):(\d\d):(\d\d),(\d\d\d)", timestr)
        if m is not None:
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3))
            milliseconds = int(m.group(4))
            return dt.timedelta(
                hours=hours, minutes=minutes, seconds=seconds,
                milliseconds=milliseconds
            )
        else:
            raise ValueError("Wrong srt time format")
    if extension == "ass":
        m = re.match(r"(\d):(\d\d):(\d\d).(\d\d)", timestr)
        if m is not None:
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3))
            milliseconds = int(m.group(4)) * 10
            return dt.timedelta(
                hours=hours, minutes=minutes, seconds=seconds,
                milliseconds=milliseconds
            )
        else:
            raise ValueError("Wrong ass time format")
    else:
        raise ValueError("Unsupported file extension")


def calculate_start_time(file_path):
    """Calculate the time of the first line in subtitle file.
       Return timedelta object."""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(ASS_REGEX, line)
            if "-->" in line:
                start, _ = line.split("-->")
                start = timestr_to_timedelta(start.strip(), "srt")
                return start
            elif m is not None:
                start = m.group(2)
                start = timestr_to_timedelta(start.strip(), "ass")
                return start
    raise ValueError("Start time wasn't calculated")


def display_delta(delta, file_path):
    """Represent timedelta object as a string."""
    return f"{file_path}: {delta.seconds},{delta.microseconds // 1000} seconds"


sub_files = [
    file_path for file_path in os.listdir()
    if os.path.splitext(file_path)[1] in (".srt", ".ass")
]


if args.first or args.f_min:
    print("First line starts at:")
    if args.file_number is not None:
        times = []
        for file_number, file_path in enumerate(sub_files, start=1):
            if file_number in args.file_number:
                times.append((calculate_start_time(file_path), file_path))
    else:
        times = [(calculate_start_time(file_path), file_path) for file_path in sub_files]
    if args.f_min:
        delta, file_path = min(times)
        print(display_delta(delta, file_path))
    else:
        for time in times:
            delta, file_path = time
            print(display_delta(delta, file_path))
    parser.exit()


# By how much to shift subtitles as a timedelta object
TIME_DELTA = dt.timedelta(seconds=args.seconds, milliseconds=args.millisec)


def shift_time(timestr, extension):
    """Shift time of a given timestring and return new timestring."""
    timedelta_obj = timestr_to_timedelta(timestr, extension)
    timedelta_obj = timedelta_obj + TIME_DELTA
    if timedelta_obj < MIN_TIME:
        raise ValueError("Time cannot be shifted more than to zero")
    hours = timedelta_obj.days * 24 + timedelta_obj.seconds // 3600
    minutes = (timedelta_obj.seconds % 3600) // 60
    seconds = timedelta_obj.seconds % 3600 % 60
    milliseconds = timedelta_obj.microseconds // 1000
    if extension == "srt":
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    if extension == "ass":
        return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds//10:02}"


def handle_srt(file_path):
    temp_lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if line_number < args.line:
                temp_lines.append(line)
            elif "-->" in line:
                start, finish = line.split("-->")
                start = shift_time(start.strip(), "srt")
                finish = shift_time(finish.strip(), "srt")
                temp_lines.append(f"{start} --> {finish}\n")
            else:
                temp_lines.append(line)
    with open(file_path, "w", encoding="utf-8") as f:
        for line in temp_lines:
            f.write(line)


def handle_ass(file_path):
    temp_lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            m = re.match(ASS_REGEX, line)
            if line_number < args.line:
                temp_lines.append(line)
            elif m is not None:
                start, finish = m.group(2), m.group(3)
                start = shift_time(start.strip(), "ass")
                finish = shift_time(finish.strip(), "ass")
                temp_lines.append(
                    f"{m.group(1)}{start},{finish},{m.group(4)}\n"
                )
            else:
                temp_lines.append(line)
    with open(file_path, "w", encoding="utf-8") as f:
        for line in temp_lines:
            f.write(line)


if args.file_number is not None:
    for file_number, file_path in enumerate(sub_files, start=1):
        if file_number in args.file_number:
            _, ext = os.path.splitext(file_path)
            if ext == ".srt":
                handle_srt(file_path)
            if ext == ".ass":
                handle_ass(file_path)
else:
    for file_path in sub_files:
        _, ext = os.path.splitext(file_path)
        if ext == ".srt":
            handle_srt(file_path)
        if ext == ".ass":
            handle_ass(file_path)
