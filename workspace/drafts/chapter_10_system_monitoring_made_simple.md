# Chapter 10: System Monitoring Made Simple

System administration, DevOps, and deployment monitoring have historically been dominated by tools created in the 1970s and 1980s. When a server spikes in CPU usage or a deployment silently fills up disk space, the traditional response involves a flurry of cryptic `ps`, `top`, and `du` commands. While these legacy tools get the job done, they often output dense, unformatted walls of text that take time to parse mentally—time you don't have during an active incident.

In this chapter, we will explore the modern approach to system monitoring. We will replace archaic sysadmin utilities with next-generation, Rust-based alternatives that provide instant visual feedback, sensible defaults, and a much gentler learning curve.

## Understanding System Processes with `procs`

If you've ever needed to find a misbehaving application or check if a web server is running after a deployment, you've likely used `ps aux | grep <process>`. This combination of commands is a rite of passage, but it's undeniably clunky. The output is monochromatic, column headers are easily misaligned, and remembering the flags (`aux` vs `-ef`) is a chore.

Enter `procs`, a modern replacement for `ps` written in Rust.

### Why `procs`?
`procs` reimagines process management by adding:
* **Automatic Colorization:** Different colors for users, memory usage, and states.
* **Human-Readable Formats:** Memory is displayed in MB/GB instead of raw kilobytes.
* **Built-in Search:** No need to pipe to `grep` anymore.
* **Docker Integration:** It can show you which container a process belongs to—an absolute lifesaver for modern deployment and CI/CD troubleshooting.

### Usage Examples

To list all processes, simply run:
```bash
procs
```

To search for a specific process (e.g., `node`), you don't need `grep`. Just pass the keyword:
```bash
procs node
```

Want a tree view to see parent-child relationships? 
```bash
procs --tree
```
This is incredibly useful when tracing how a background worker or a CI/CD runner was spawned.

## Analyzing Disk Space Visually with `dust`

"Disk full" (Error: No space left on device) is one of the most common and frustrating deployment issues. Traditionally, you would hunt down large directories using `du -sh *` or an interactive tool like `ncdu`. 

`dust` (a clever play on `du` + `Rust`) offers a far more intuitive approach. It visually maps your directory sizes using a tree hierarchy and percentage bars, instantly guiding your eyes to the largest space hogs.

### Usage Examples

To analyze the current directory:
```bash
dust
```

The output gives you an immediate visual representation of which folders are consuming the most space, without needing to sort or filter manually. It is fast, respects `.gitignore` rules if you want it to, and handles massive directories gracefully.

If you only want to see 3 levels deep:
```bash
dust -d 3
```

## Flexing Your System Information with `fastfetch`

Sometimes you just need a quick summary of the system you are working on—whether it's a new cloud VM, a CI build agent, or your local machine. What OS version is running? Which kernel? How much RAM is available?

While tools like `uname -a` or `cat /etc/os-release` exist, `fastfetch` provides a beautiful, instant dashboard of your system's vital statistics. It is the modern, highly optimized successor to `neofetch`.

### Usage Examples

Just run:
```bash
fastfetch
```

Instantly, you get an aesthetically pleasing breakdown of your hardware, OS, kernel, uptime, shell, and memory usage. It's not just for aesthetics; it's a genuinely fast way to orient yourself and verify system resources when SSHing into a new environment.

## Summary

System monitoring doesn't have to be a dark art requiring a cheat sheet. By upgrading your toolbelt to include `procs`, `dust`, and `fastfetch`, you gain instant, visual, and intuitive observability into your machine's state, drastically reducing your mean time to resolution (MTTR) when things go wrong.