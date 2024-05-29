# Bisector - `git bisect` without git

This is a simple tool / library that lets you have functionality similar to [`git bisect`](https://git-scm.com/docs/git-bisect), but for an arbitrary list of options
that is not confined to a git repository. This allows you to easily answer questions such as "when did X start happening?" or
"what was the first thing that broke Y?".

This library is extremely WIP. Note features that would be nice to have are listed at the end of the README, in [Future Work](#future-work).

>[!NOTE]
> This uses git-like terminology: every option is either labelled "good" or "bad", and the goal is to find the first "bad" option.
> Label any option that doesn't match your criteria as "good", and any option that does as "bad".

## Example Usages

Say you have 100 files named sequentially, and you want to find the first file that contains "hello" in it:

```shell
dir/001.txt
dir/002.txt
...
dir/063.txt  # this and all files after it contain "hello"
...
dir/100.txt
```

### Manually bisecting

Start the bisecting session:

```shell
$ bisector start -f <(ls -v dir/*.txt)  # file with options
# or
$ ls -v dir/*.txt | bisector start      # pipe options
[+] Current option [@index: 50]: dir/050.txt
```

Then, check the suggested option `dir/050.txt`. In this case, it doesn't contain "hello", so you can tell the bisector it is the "good" option:

```shell
$ bisector good
[+] Current option [@index: 76]: dir/076.txt
```

Now, check the next option, `dir/076.txt`. This one contains "hello", so you can tell the bisector it is the "bad" option:

```shell
$ bisector good
[+] Current option [@index: 63]: dir/063.txt
```

And then you keep going, until:

```shell
$ bisector good
[+] Finished session, result: BisectionResult.FOUND_BAD, value: dir/063.txt [@index: 63]
```

### Automating the process

If the process of checking each option can be automated, you can use the `run` subcommand to provide a command that
automatically checks each option. The option (*not* the index) will be passed as an extra argument to the end of the command.
Generally, you should use a script here for any non-trivial command that can't take in the option as the last argument.

If the command exits with a status code of 0, the option is considered "good". Otherwise, it is considered "bad". Like
for `git bisect run`, exit code `125` is considered "skip" (unsupported in this version).

```shell
$ ls -v dir/*.txt | bisector run grep -v "hello"  # will exit with 0 for files without "hello"
before ... 50
before ... 57
before ... 60
before ... 62
[+] Finished session, result: BisectionResult.FOUND_BAD, value: dir/063.txt [@index: 63]
```

Here's the same thing, but with a script:

```shell
$ cat check.py
import sys
exit("hello" in open(sys.argv[1]).read())

$ ls -v dir/*.txt | bisector run python check.py
[+] Finished session, result: BisectionResult.FOUND_BAD, value: dir/063.txt [@index: 63]
```

### As a library

You can also import `bisector` as a library and get access to a `Bisector` class that you can use to bisect any list of options:

```py
from bisector import Bisector, Status
from glob import glob

# Sorting the options is important!
b = Bisector(sorted(glob("dir/*.txt")))
while not b.is_done():
    option = b.current
    if "hello" in open(option).read():
        b.set_bad()
    else:
        # NOTE: good means "doesn't contain hello"
        b.set_good()
result, value = b.get_result()
print(f"Result: {result}, value: {value}")

# Output: `Result: BisectionResult.FOUND_BAD, value: dir/063.txt`
```

Alternatively, if you can express the logic as a function that takes an option and returns a `Status`, you can
use the `run_bisect` function:

```py
from bisector import run_bisect, Status

def check_hello(option):
    if "hello" in open(option).read():
        return Status.BAD
    return Status.GOOD

options = sorted(glob("dir/*.txt"))
result, value = run_bisect(options, check_hello)
print(f"Result: {result}, value: {value}")

# Output: `Result: BisectionResult.FOUND_BAD, value: dir/063.txt`
```

## Future Work

- [ ] Add support for `skip` in the Bisector class
  - Note: this is non-trivial, we want to make sure we can find the error even if most of the options are skipped,
    as long as we can find one bad option following a good one.
- [ ] Add support for customizing known "good" and "bad" labels from CLI, when we don't want to a range of options only
- [ ] Better logging / help messages
- [ ] Keep track of actions and add ability to replay a session
- [ ] Ability to visualize the current bisecting session
- [ ] Reset command to reset the current session
- [ ] Show approximately how many steps are left (similar to `git bisect`)
- [ ] More robust testing for the library / CLI
- [ ] Ability to customize (per session / globally) the terms "good" and "bad"