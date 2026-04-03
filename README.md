# Python Data Streams
Manipulate pickled Python objects through shell pipes `🐍|🥒`


# What it is
pds is a command-line tool to create python-based pipelines in the shell. It comes in handy if you are more of a 
Python expert than a shell expert, and can replace complex shell scripts and/or pipelines (grep, sed, awk, tr, sort...) 
with more readable (but also more wordy) commands.

The main differences compared to other "python code in the command line" tools such as pyp, pyped, pythonpy etc. are:
1. Python objects are sent directly through the pipelines instead of text
    * this is more robust, and reduces the need to deal with quirks of textual representation (encodings, whitespace and quoting etc.)
    * it is also more convenient, as object methods can be called directly
2. Lots of built-in "modes" (commands) require less typing and lead to more expressive command chains
3. Using shell pipelines directly allows complex commands to be developed incrementally by appending to the existing chain
4. "Text" vs. "Python object" input/output selection for ~smooth interaction with exiting tools
5. JSON input/output makes it easy to manipulate JSON data directly (no need to learn `jq`)
6. Works on Linux and Windows


# Examples
This section lists some examples of pds pipelines, together with their equivalent shell equivalents (for Linux and Windows)

## Count non-empty lines in a file
```bash
# grep -cve "^\s*$" pds.py
# findstr /R /V "^$" pds.py | find /C /V ""
cat pds.py | pds filter "x.strip()" | pds count
```

## Print the name and size of the 5 largest files in the current directory and subdirectories
```bash
# find . -type f -exec du -h {} + | sort -hr | head -n 5
# cmd.exe: ???
pds files -R | pds filter "x.is_file()" | pds each "x, x.stat().st_size" | pds sort -r "x[1]" | pds iter "islice(it, 5")
```

## Copy the 3 most recent .zip files to /some/where
```bash
# find . -maxdepth 1 -name "*.zip" -type f -printf '%T@\t%p\n' | sort -k1,1nr | head -n 3 | cut -f2- | xargs -r -I {} cp {} /some/where
# cmd.exe: ???
pds files *.zip | pds sort "x.stat().st_ctime" | pds list "l[-3:]" | pds each "shutil.copy(x, r'/some/where')"
```

## Kill all python processes of the current user
```bash
# pkill -9 -u "$USER" python
# TASKKILL /IM python.exe /F
pds procs -U | pds filter -E "x.name() == 'python'" | pds each "x.kill()"
```

## List all users (sorted alphabetically) who have python3 processes running on this machine
```bash
# Note: this bash version is not very robust, e.g. a user named "python3" will break it!
# ps -eo user,comm | grep python3 | awk '{print $1}' | sort -u
# cmd.exe: ???
pds procs | pds filter -Eq "x.name() == 'python3'" | pds each -Eq "x.username()" | pds iter set(it) | pds sort

# Alternate form using `jc ps` instead of `pds procs`
jc ps -eo user,comm | pds --input=json filter "x['command'] == 'python3'" | pds each "x['user']" | pds iter "set(it)" | pds sort
```


# Is it fast?
Not really 😐

The implementation is pure python and does a lot of pickling/unpickling, so if you are piping a large amount of objects and/or you 
care about execution speed, resource usage etc. then **pds** is probably not a good choice.


# Open TODOs
 * Additional input/output types: `csv`, ...
 * Additional modes: `apply`, `check`, `flatten`, ...
 * Improved exception handling
 * Parallel execution
 * ...