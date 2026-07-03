# Chapter 4: Viewing Files with Style

Once you have navigated to a directory, your immediate next step is almost always to see what is inside it. For this, users have historically relied on `ls` to list directory contents and `cat` to read files.

While these tools are functional, they are visually bland. In a modern development environment, context is everything. We want to know not just what files exist, but their sizes in human-readable formats, their icons, and their Git tracking status. When we read a file, we expect syntax highlighting, not a monochromatic wall of text.

In this chapter, we will replace `ls` and `cat` with two modern powerhouses: **`eza`** and **`bat`**.

## Eza: A Modern `ls` Replacement

**`eza`** is a direct drop-in replacement for the `ls` command. It takes everything good about listing directories and supercharges it with colors, icons, and Git integration.

### Installation
On macOS (Homebrew):
```bash
brew install eza
```
On Linux (Ubuntu/Debian):
```bash
sudo apt install eza
```

### Git-Aware, Colorful Listings

When you type `ls`, you get a plain list of names. When you type `eza`, the output is automatically color-coded based on file types (directories are blue, executables are green, archives are red).

But `eza` truly shines with its flags:

```bash
# The basic long-format listing
eza -l
```

Instead of chaotic column widths, `eza -l` perfectly aligns file sizes, permissions, and modification dates. It even displays file sizes in human-readable formats (e.g., `1.2M` instead of `1248000`) by default.

Want to see Git status? Use the `--git` flag:
```bash
eza -l --git
```
This adds a column showing exactly which files are staged (`+`), modified (`M`), or untracked (`?`), acting as a mini `git status` right in your directory listing.

### The Tree View

One of the most powerful features of `eza` is its built-in tree view. Instead of installing a separate `tree` command, you can use:
```bash
eza --tree --level=2
```
This prints a beautiful, structured hierarchy of your folders, up to two levels deep, complete with color coding.

## Bat: A Cat with Wings

The traditional `cat` command simply prints the contents of a file to your screen. If you print a 300-line JSON file, it spits out raw text and overwhelms your terminal.

**`bat`** is an advanced replacement for `cat` that brings IDE-like features directly to your command line.

### Installation
```bash
brew install bat  # macOS
sudo apt install bat  # Ubuntu/Linux
```

### Syntax Highlighting in the Terminal

When you use `bat` to read a file, it automatically detects the programming language or file format and applies gorgeous syntax highlighting.

```bash
bat package.json
```

By default, `bat` includes:
1. **Syntax Highlighting:** Makes code instantly readable.
2. **Line Numbers:** Essential for debugging and pairing with error messages.
3. **Git Integration:** Displays a sidebar indicating lines that have been added, modified, or removed compared to your Git index.
4. **Automatic Paging:** If a file is longer than your screen, `bat` automatically pipes the output into a "pager" (like `less`), allowing you to scroll through the file using your arrow keys instead of flooding your terminal history.

By swapping `ls` for `eza` and `cat` for `bat`, your terminal will feel less like a 1970s mainframe and more like a modern, fully-featured code editor.