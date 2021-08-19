# CLI subtitle redactor

A CLI tool to shift subtitle timings. It should be added to the path and run from the directory where subtitles are located.
Keep backup copies of files, all changes are final.

Options:

`-f, --first` Print out the time of the first line in seconds.

`-s, --seconds` Shift all lines by given amount of seconds.

`-m, --millisec` Shift all lines by given amount of milliseconds.

`--f-min` Print out the minimum time of the first line in seconds among selected files or among all files if none selected.

`-l, --line` Shift all lines starting from provided line number in the file. First line has number 1.

`-n, --file-number` Ordinal number of subtitle files that will be modified. Has no connection to the number in filename. Only subtitle files are counted. First file has number 1.
