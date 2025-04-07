# jit
Another oddly familiar sounding version control system to ruin everyones day

It works pretty much like the big boys - git and merc - but yeah not as many commands or new things. It also is completely local, and doesnt have a hub like, you know, git.

## ☝🤓 Why I decided to make this
So like i decided i should get better at git. Ofc, the next logical step to do that would be to create git right? Yeah obviously duh, so i decided i should do that. Now i have a half baked version of git that i call jit because its supposed to be a play on the gif/jif thing and I am equally more confused about git as i am with jit 😊👍.

In all honesty though, this is supposed to be a fun project, and nothing serious, it might break, so use it at your own peril.

- ALSO I JUST REALIZED THIS BUT I AM MAKING THIS PUBLIC LITERALLY EXACTLY 20 YEARS AFTER LINUS' FIRST EVER COMMIT LMAOOOO 
go check it out: 
https://github.com/git/git/commit/e83c5163316f89bfbde7d9ab23ca2e25604af290

## Installation

### From Source
```bash
git clone https://github.com/username/jit.git
cd jit
# Run directly with Python
python jit/main.py <command>
```
or if you want to install it, like a normal person should

```bash
git clone https://github.com/username/jit.git
cd jit
# Run directly with Python
pip install -e .     #this is for development
pip install .        #this is for actual, but why even would one unless they want linus and me to have a dual (linus spare me i am out of my element here)
```

## 🛠️ Available Commands

### 🚧 Initialize a Repository
```bash
jit init
```

### 🔁 Track Files
```bash
jit add <file_path>     # Add a specific file
jit add .               # Add all changed files in directory
```

### ✍️ Commit Changes
```bash
jit commit -m "Your commit message here"
```

### 📜 View Commit History
```bash
jit log                 # Show commit logs for current branch
jit log --all           # Show commit logs from all branches
```

### 🌱 Branch Management
```bash
jit branch <name>       # Create a new branch
jit branches            # List all branches
jit checkout <branch>   # Switch to a branch
jit checkout -b <branch> # Create and switch to a new branch
```

### 💡 Check Status
```bash
jit status              # Show the working tree status
```

### 🔧 Restoring and Reverting
```bash
jit restore <commit_hash>  # Restore working directory to a specific commit
jit rm <file_path>         # Remove file and stage deletion
jit rm -f <file_path>      # Force remove file even if not tracked
```

### 🧹 Clean Workspace
```bash
jit clean               # Show untracked files that would be removed
jit clean -f            # Remove untracked files without prompt
```

### 🚧 Future Features
I dont think i will get to it, maybe i will, who knows (i do, and no i dont think so)
```bash
jit push                
jit pull 
jit fetch
jit merge
# whatever else yall can think of
```


## 🤔 Why Use Jit?
Because you apparently dont like being sane and want one more version control to make things positively worse


## 🤘 Contribute or Report Issues
Feel free to fork it, PR it, or just shoot me a message if you think there's any hope of improving this mess. But in all honesty, let’s face it, it’s probably (im)perfect the way it is.
