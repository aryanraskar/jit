#!/usr/bin/env python3

import os
import hashlib
import time
import json
import sys
from colorama import init, Fore, Style

init(autoreset=True)

JIT_DIR = '.jit'
OBJECTS_DIR = f'{JIT_DIR}/objects'
REFS_DIR = f'{JIT_DIR}/refs/heads'
HEAD_FILE = f'{JIT_DIR}/HEAD'
INDEX_FILE = f'{JIT_DIR}/index'
CONFIG_FILE = f'{JIT_DIR}/config'
LOGS_DIR = f'{JIT_DIR}/logs'

DEFAULT_IGNORE_PATTERNS = [
    '.jit/',
    '.DS_Store',
    '__pycache__/',
    '*.pyc',
    '.vscode/',
    '.git/'
]

def success(msg):
    return f"{Fore.GREEN}{msg}{Style.RESET_ALL}"

def error(msg):
    return f"{Fore.RED}{msg}{Style.RESET_ALL}"

def warning(msg):
    return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"

def info(msg):
    return f"{Fore.BLUE}{msg}{Style.RESET_ALL}"

def highlight(msg):
    return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"

def bold(msg):
    return f"{Style.BRIGHT}{msg}{Style.RESET_ALL}"

def init_jit():
    os.makedirs(OBJECTS_DIR, exist_ok=True)
    os.makedirs(REFS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    with open(HEAD_FILE, 'w') as f:
        f.write('ref: refs/heads/main')

    with open(INDEX_FILE, 'w') as f:
        f.write(json.dumps({}))

    with open(CONFIG_FILE, 'w') as f:
        f.write('')
    
    with open(f'{REFS_DIR}/main', 'w') as f:
        f.write('')
    
    # Create default .gitignore file - add a flag for this to ignore this command
    create_gitignore()
    
    print("Initialized empty Jit repository")
    print("Repository ready for your first commit")

def create_gitignore():
    if os.path.exists('.gitignore'):
        return
    
    with open('.gitignore', 'w') as f:
        for pattern in DEFAULT_IGNORE_PATTERNS:
            f.write(f"{pattern}\n")

def hash_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
            is_binary = False
    except UnicodeDecodeError:
        with open(file_path, 'rb') as f:
            data = f.read()
            data = data.hex() 
            is_binary = True
            
    file_hash = hashlib.sha1(data.encode() if not is_binary else bytes.fromhex(data)).hexdigest()
    
    return file_hash, data, is_binary

def store_object(data, is_binary=False):
    content = data if not is_binary else data.encode('utf-8')
    obj_hash = hashlib.sha1(content if is_binary else content.encode()).hexdigest()
    
    obj_path = os.path.join(OBJECTS_DIR, obj_hash)
    if not os.path.exists(obj_path):
        with open(obj_path, 'wb' if is_binary else 'w', encoding=None if is_binary else 'utf-8') as f:
            f.write(content if is_binary else data)
    
    return obj_hash

def read_index():
    try:
        with open(INDEX_FILE, 'r') as f:
            return json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_index(index):
    with open(INDEX_FILE, 'w') as f:
        f.write(json.dumps(index))

def get_current_branch_and_commit():
    if not os.path.exists(HEAD_FILE):
        return None, None
        
    with open(HEAD_FILE, 'r') as f:
        head_content = f.read().strip()
    
    if head_content.startswith('ref: '):
        ref_path = head_content[5:]  
        branch_name = ref_path.split('/')[-1]
        
        branch_file = f"{JIT_DIR}/{ref_path}"
        if os.path.exists(branch_file):
            with open(branch_file, 'r') as f:
                commit_hash = f.read().strip()
        else:
            commit_hash = ""
    else:
        branch_name = None
        commit_hash = head_content
    
    return branch_name, commit_hash

def get_tracked_files():
    _, commit_hash = get_current_branch_and_commit()
    tracked_files = {}
    
    if commit_hash:
        commit_file = f"{OBJECTS_DIR}/{commit_hash}"
        if os.path.exists(commit_file):
            with open(commit_file, 'r') as f:
                commit_data = json.loads(f.read())
                
            for file_path, file_info in commit_data.get('tree', {}).items():
                if not file_info.get('deleted', False):
                    tracked_files[file_path] = file_info
    
    return tracked_files

def should_ignore_file(file_path):
    file_path = os.path.normpath(file_path)
    
    if file_path.startswith(JIT_DIR) or JIT_DIR in file_path:
        return True
    
    for pattern in DEFAULT_IGNORE_PATTERNS:
        if pattern.endswith('/'):
            if pattern[:-1] in file_path.split(os.sep):
                return True
        elif pattern.startswith('*'):
            if file_path.endswith(pattern[1:]):
                return True
        elif pattern in file_path:
            return True
    
    # TODO: Add support for reading .gitignore file patterns
    
    return False

def add_file(file_path):
    file_path = os.path.normpath(file_path)
    
    if not os.path.exists(file_path):
        tracked_files = get_tracked_files()
        if file_path in tracked_files:
            index = read_index()
            index[file_path] = {
                'deleted': True,
                'timestamp': time.time()
            }
            write_index(index)
            print(f"Staged deletion of '{file_path}'")
        else:
            print(f"Error: '{file_path}' did not match any files")
        return
    
    if should_ignore_file(file_path):
        print(f"Ignoring '{file_path}' (matches ignore pattern)")
        return
    
    file_hash, data, is_binary = hash_file(file_path)
    
    store_object(data, is_binary)
    
    index = read_index()
    index[file_path] = {
        'hash': file_hash,
        'timestamp': time.time(),
        'binary': is_binary
    }
    write_index(index)
    
    tracked_files = get_tracked_files()
    if file_path in tracked_files:
        status = "modified"
    else:
        status = "new file"
        
    print(f"Staged {status}: '{file_path}'")

def add_all_changes():
    status = get_status()
    
    for file_path in status['modified']:
        add_file(file_path)
    
    for file_path in status['deleted']:
        add_file(file_path) 

    for file_path in status['untracked']:
        add_file(file_path)
    
    if not any((status['modified'], status['deleted'], status['untracked'])):
        print("No changes to add")

def remove_file(file_path, force=False):
    file_path = os.path.normpath(file_path)
    
    tracked_files = get_tracked_files()
    is_tracked = file_path in tracked_files
    
    if not is_tracked and not force:
        print(f"Error: '{file_path}' is not tracked")
        return False
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Removed '{file_path}' from workspace")
        except Exception as e:
            print(f"Error removing '{file_path}': {e}")
            return False
    
    if is_tracked:
        index = read_index()
        index[file_path] = {
            'deleted': True,
            'timestamp': time.time()
        }
        write_index(index)
        print(f"Staged deletion of '{file_path}'")
        return True
    
    return False

def commit_changes(message):
    index = read_index()
    
    if not index:
        print("Nothing to commit, working tree clean")
        return None
        
    branch_name, parent_commit = get_current_branch_and_commit()
    if not branch_name:
        print("Error: Cannot commit in detached HEAD state")
        return None
    
    tree = {}
    for file_path, file_info in index.items():
        tree[file_path] = file_info
    
    commit_data = {
        'message': message,
        'parent': parent_commit if parent_commit else None,
        'timestamp': time.time(),
        'tree': tree
    }
    
    commit_json = json.dumps(commit_data)
    commit_hash = store_object(commit_json)
    
    with open(f'{REFS_DIR}/{branch_name}', 'w') as f:
        f.write(commit_hash)
    
    write_index({})
    
    added = sum(1 for info in tree.values() if not info.get('deleted', False))
    deleted = sum(1 for info in tree.values() if info.get('deleted', False))
    
    print(f"[{commit_hash[:7]}] {message}")
    print(f" {added} file(s) changed, {deleted} deletion(s)")
    
    return commit_hash

def get_status():
    tracked_files = get_tracked_files()
    
    index = read_index()
    
    status = {
        'staged_new': [],
        'staged_modified': [],
        'staged_deleted': [],
        'modified': [],
        'deleted': [],
        'untracked': []
    }
    
    for file_path, file_info in index.items():
        if file_info.get('deleted', False):
            status['staged_deleted'].append(file_path)
        elif file_path not in tracked_files:
            status['staged_new'].append(file_path)
        else:

            if file_info['hash'] != tracked_files[file_path]['hash']:
                status['staged_modified'].append(file_path)
    
    for root, dirs, files in os.walk('.'):
        if JIT_DIR in dirs:
            dirs.remove(JIT_DIR) 
        
        for file in files:
            file_path = os.path.normpath(os.path.join(root, file))
            
            if should_ignore_file(file_path):
                continue
                
            if file_path in index:
                if not index[file_path].get('deleted', False):
                    file_hash, _, _ = hash_file(file_path)
                    if file_hash != index[file_path]['hash']:
                        status['modified'].append(file_path)
            elif file_path in tracked_files:
                file_hash, _, _ = hash_file(file_path)
                if file_hash != tracked_files[file_path]['hash']:
                    status['modified'].append(file_path)
            else:
                status['untracked'].append(file_path)
    
    for file_path in tracked_files:
        if file_path not in index and not os.path.exists(file_path):
            status['deleted'].append(file_path)
    
    return status

def show_status():
    branch_name, commit_hash = get_current_branch_and_commit()
    
    if branch_name:
        print(f"On branch {Fore.GREEN}{branch_name}{Style.RESET_ALL}")
    else:
        print(f"HEAD detached at {highlight(commit_hash[:7])}")
    
    status = get_status()
    
    if any((status['staged_new'], status['staged_modified'], status['staged_deleted'])):
        print(f"\n{success('Changes to be committed:')}")
        for file_path in status['staged_new']:
            print(f"  {Fore.GREEN}new file:   {file_path}{Style.RESET_ALL}")
        for file_path in status['staged_modified']:
            print(f"  {Fore.YELLOW}modified:   {file_path}{Style.RESET_ALL}")
        for file_path in status['staged_deleted']:
            print(f"  {Fore.RED}deleted:    {file_path}{Style.RESET_ALL}")
    
    if any((status['modified'], status['deleted'])):
        print(f"\n{warning('Changes not staged for commit:')}")
        for file_path in status['modified']:
            print(f"  {Fore.YELLOW}modified:   {file_path}{Style.RESET_ALL}")
        for file_path in status['deleted']:
            print(f"  {Fore.RED}deleted:    {file_path}{Style.RESET_ALL}")
    
    if status['untracked']:
        print(f"\n{info('Untracked files:')}")
        for file_path in status['untracked']:
            print(f"  {Fore.CYAN}{file_path}{Style.RESET_ALL}")
    
    if not any(status.values()):
        print(f"\n{success('Working tree clean')}")

def show_log():
    _, current_commit = get_current_branch_and_commit()
    
    if not current_commit:
        print(info("No commits yet"))
        return
    
    commit_hash = current_commit
    visited = set()
    
    print(bold("Commit history:"))
    while commit_hash and commit_hash not in visited:
        commit_path = f"{OBJECTS_DIR}/{commit_hash}"
        if not os.path.exists(commit_path):
            print(error(f"Error: Commit {commit_hash} not found"))
            break
            
        with open(commit_path, 'r') as f:
            commit_data = json.loads(f.read())
        
        print(f"{Fore.YELLOW}Commit: {highlight(commit_hash)}")
        print(f"Date:    {Style.DIM}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(commit_data['timestamp']))}{Style.RESET_ALL}")
        print(f"Message: {bold(commit_data['message'])}")
        
        added_files = []
        modified_files = []
        deleted_files = []
        for file_path, file_info in commit_data['tree'].items():
            if file_info.get('deleted', False):
                deleted_files.append(file_path)
            elif commit_data.get('parent'):
                modified_files.append(file_path)
            else:
                added_files.append(file_path)
        
        if added_files:
            print(f"{Fore.GREEN}Added files (+):{Style.RESET_ALL}")
            for file in added_files:
                print(f"  {Fore.GREEN}{file}{Style.RESET_ALL}")
        
        if modified_files:
            print(f"{Fore.YELLOW}Modified files (~):{Style.RESET_ALL}")
            for file in modified_files:
                print(f"  {Fore.YELLOW}{file}{Style.RESET_ALL}")
        
        if deleted_files:
            print(f"{Fore.RED}Deleted files (-):{Style.RESET_ALL}")
            for file in deleted_files:
                print(f"  {Fore.RED}{file}{Style.RESET_ALL}")
        
        print()
        commit_hash = commit_data.get('parent')
        visited.add(commit_hash)

def show_all_logs():
    if not os.path.exists(REFS_DIR):
        print("No branches found")
        return
    
    branches = {}
    for branch in os.listdir(REFS_DIR):
        branch_path = f"{REFS_DIR}/{branch}"
        if os.path.isfile(branch_path):
            with open(branch_path, 'r') as f:
                commit_hash = f.read().strip()
                if commit_hash:
                    branches[branch] = commit_hash
    
    if not branches:
        print("No commits found in any branch")
        return
    
    current_branch, _ = get_current_branch_and_commit()
    
    all_commits = {}
    branch_tips = {}
    
    for branch_name, tip_commit in branches.items():
        commit_hash = tip_commit
        visited = set()
        
        while commit_hash and commit_hash not in visited:
            commit_path = f"{OBJECTS_DIR}/{commit_hash}"
            if not os.path.exists(commit_path):
                break
                
            visited.add(commit_hash)
            
            with open(commit_path, 'r') as f:
                commit_data = json.loads(f.read())
            
            if commit_hash not in all_commits:
                all_commits[commit_hash] = {
                    'data': commit_data,
                    'branches': []
                }
            
            if commit_hash == tip_commit:
                all_commits[commit_hash]['branches'].append(branch_name)
                branch_tips[branch_name] = commit_hash
            
            commit_hash = commit_data.get('parent')
    
    sorted_commits = sorted(
        all_commits.items(),
        key=lambda x: x[1]['data']['timestamp'],
        reverse=True
    )
    
    print("All commits across branches:")
    print("===========================")
    
    for commit_hash, commit_info in sorted_commits:
        commit_data = commit_info['data']
        branches_str = ""
        
        if commit_info['branches']:
            branch_labels = []
            for branch in commit_info['branches']:
                if branch == current_branch:
                    branch_labels.append(f"*{branch}")
                else:
                    branch_labels.append(branch)
            branches_str = f" ({', '.join(branch_labels)})"
        
        print(f"Commit: {commit_hash}{branches_str}")
        print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(commit_data['timestamp']))}")
        print(f"Message: {commit_data['message']}")
        
        added_files = 0
        modified_files = 0
        deleted_files = 0
        for file_info in commit_data['tree'].values():
            if file_info.get('deleted', False):
                deleted_files += 1
            else:
                if commit_data.get('parent'):
                    modified_files += 1
                else:
                    added_files += 1
        
        print(f"Changes: +{added_files} ~{modified_files} -{deleted_files}")
        print()
    
    print("Legend:")
    print("* - current branch")

def create_branch(branch_name):
    if os.path.exists(f"{REFS_DIR}/{branch_name}"):
        print(f"Error: Branch '{branch_name}' already exists")
        return False
    
    _, current_commit = get_current_branch_and_commit()
    
    with open(f"{REFS_DIR}/{branch_name}", 'w') as f:
        f.write(current_commit if current_commit else '')
    
    print(f"Created branch '{branch_name}' at {current_commit[:7] if current_commit else 'HEAD'}")
    return True

def list_branches():
    if not os.path.exists(REFS_DIR):
        print(error("No branches found"))
        return
    
    branches = []
    for branch in os.listdir(REFS_DIR):
        branch_path = f"{REFS_DIR}/{branch}"
        if os.path.isfile(branch_path):
            branches.append(branch)
    
    if not branches:
        print(info("No branches found"))
        return
    
    current_branch, _ = get_current_branch_and_commit()
    
    print(bold("Branches:"))
    for branch in branches:
        with open(f"{REFS_DIR}/{branch}", 'r') as f:
            commit = f.read().strip()
        
        if branch == current_branch:
            print(f"{Fore.GREEN}* {branch}{Style.RESET_ALL} (current) - {commit[:7] if commit else ''}")
        else:
            print(f"  {Fore.CYAN}{branch}{Style.RESET_ALL} - {commit[:7] if commit else ''}")

def restore_file_from_commit(file_path, file_info):
    if file_info.get('deleted', False):
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    
    obj_path = f"{OBJECTS_DIR}/{file_info['hash']}"
    if not os.path.exists(obj_path):
        print(f"Error: Object {file_info['hash']} not found")
        return
    
    with open(obj_path, 'r', encoding='utf-8') as f:
        data = f.read()
    
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    is_binary = file_info.get('binary', False)
    if is_binary:
        with open(file_path, 'wb') as f:
            f.write(bytes.fromhex(data))
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)

def checkout_branch(branch_name, create=False):
    if create:
        if os.path.exists(f"{REFS_DIR}/{branch_name}"):
            print(f"Error: Branch '{branch_name}' already exists")
            return False
        create_branch(branch_name)
    
    branch_path = f"{REFS_DIR}/{branch_name}"
    if not os.path.exists(branch_path):
        print(f"Error: Branch '{branch_name}' does not exist")
        return False
    
    index = read_index()
    if index:
        print("Error: You have uncommitted changes. Commit or stash them before switching branches.")
        return False
    
    current_branch, _ = get_current_branch_and_commit()
    if current_branch == branch_name:
        print(f"Already on branch '{branch_name}'")
        return True
    
    with open(branch_path, 'r') as f:
        commit_hash = f.read().strip()
    
    with open(HEAD_FILE, 'w') as f:
        f.write(f"ref: refs/heads/{branch_name}")
    
    if not commit_hash:
        print(f"Switched to branch '{branch_name}' (empty branch)")
        return True
    
    commit_path = f"{OBJECTS_DIR}/{commit_hash}"
    if not os.path.exists(commit_path):
        print(f"Error: Commit {commit_hash} not found")
        return False
    
    with open(commit_path, 'r') as f:
        commit_data = json.loads(f.read())
    
    tree = commit_data.get('tree', {})
    
    current_tracked_files = set(get_tracked_files().keys())
    
    target_files = set(tree.keys())
    
    files_to_remove = current_tracked_files - target_files
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove {file_path}: {e}")
    
    for file_path, file_info in tree.items():
        restore_file_from_commit(file_path, file_info)
    
    print(f"Switched to branch '{branch_name}'")
    return True

def restore_commit(commit_hash):
    commit_path = f"{OBJECTS_DIR}/{commit_hash}"
    if not os.path.exists(commit_path):
        print(f"Error: Commit {commit_hash} not found")
        return False
    
    with open(commit_path, 'r') as f:
        commit_data = json.loads(f.read())
    
    tree = commit_data.get('tree', {})
    
    current_tracked_files = set(get_tracked_files().keys())
    
    target_files = set(tree.keys())
    
    files_to_remove = current_tracked_files - target_files
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed {file_path}")
            except Exception as e:
                print(f"Warning: Could not remove {file_path}: {e}")
    
    for file_path, file_info in tree.items():
        restore_file_from_commit(file_path, file_info)
        if file_info.get('deleted', False):
            print(f"Deleted {file_path}")
        else:
            print(f"Restored {file_path}")
    
    print(f"Working directory restored to commit {commit_hash[:7]}")
    return True

def clean_untracked_files(force=False):
    status = get_status()
    untracked_files = status['untracked']
    
    if not untracked_files:
        print("No untracked files to clean")
        return
    
    print("The following files would be removed:")
    for file_path in untracked_files:
        print(f"  {file_path}")
    
    if not force:
        response = input("\nRemove these files? [y/N] ")
        if response.lower() != 'y':
            print("Aborting clean operation")
            return
    
    for file_path in untracked_files:
        try:
            os.remove(file_path)
            print(f"Removed {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def rebase_branch(target_branch):
    target_branch_path = f"{REFS_DIR}/{target_branch}"
    if not os.path.exists(target_branch_path):
        print(f"Error: Branch '{target_branch}' does not exist")
        return False

    current_branch, current_commit = get_current_branch_and_commit()
    if not current_branch:
        print("Error: Cannot rebase in detached HEAD state")
        return False

    with open(target_branch_path, 'r') as f:
        target_commit = f.read().strip()

    if current_commit == target_commit:
        print(f"Already up to date with '{target_branch}'")
        return True

    commits_to_replay = []
    commit_hash = current_commit
    while commit_hash and commit_hash != target_commit:
        commit_path = f"{OBJECTS_DIR}/{commit_hash}"
        if not os.path.exists(commit_path):
            print(f"Error: Commit {commit_hash} not found")
            return False
        with open(commit_path, 'r') as f:
            commit_data = json.loads(f.read())
        commits_to_replay.append((commit_hash, commit_data))
        commit_hash = commit_data.get('parent')

    if commit_hash != target_commit:
        print(f"Error: Branches do not share a common ancestor")
        return False

    commits_to_replay.reverse()
    new_parent = target_commit
    for commit_hash, commit_data in commits_to_replay:
        commit_data['parent'] = new_parent
        commit_json = json.dumps(commit_data)
        new_commit_hash = store_object(commit_json)
        new_parent = new_commit_hash

    with open(f"{REFS_DIR}/{current_branch}", 'w') as f:
        f.write(new_parent)

    print(f"Successfully rebased '{current_branch}' onto '{target_branch}'")
    return True

def main():
    if len(sys.argv) < 2:
        logo = f"""
{Fore.GREEN}     ____    _____   _____    
{Fore.GREEN}       |       |       |      
{Fore.YELLOW}       |       |       |      
{Fore.RED}       |       |       |      
{Fore.BLUE}   |___|     __|__     |      
{Fore.MAGENTA}                         {Style.RESET_ALL}v0.1
"""

        print(logo)
        print(f"Usage: {highlight('jit')} <command> [options]")
        print(f"\n{bold('Commands:')}")
        commands = [
            ("init", "Initialize jit repository"),
            ("add <file_path>", "Add file to staging area"),
            ("add .", "Add all changed files to staging area"),
            ("commit -m <message>", "Commit changes with message"),
            ("log", "Show commit logs"),
            ("log --all", "Show commit logs from all branches"),
            ("branch <name>", "Create a new branch"),
            ("branches", "List all branches"),
            ("checkout <branch>", "Switch to a branch"),
            ("checkout -b <branch>", "Create and switch to a new branch"),
            ("status", "Show working tree status"),
            ("restore <commit>", "Restore working directory to commit"),
            ("clean [-f]", "Remove untracked files"),
            ("rm <file_path>", "Remove file and stage deletion"),
            ("rebase <branch>", "Rebase current branch onto target branch"),
        ]

        max_cmd_len = max(len(cmd[0]) for cmd in commands)
        for cmd, desc in commands:
            pad = " " * (max_cmd_len - len(cmd))
            print(f"  {Fore.GREEN}{cmd}{Style.RESET_ALL}{pad}  - {desc}")
        return

    command = sys.argv[1]

    if command == "init":
        init_jit()
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: File path is required")
            return
            
        file_path = sys.argv[2]
        if file_path == ".":
            add_all_changes()
        else:
            add_file(file_path)
    
    elif command == "commit":
        message = None
        if len(sys.argv) >= 3:
            if sys.argv[2] == "-m" and len(sys.argv) >= 4:
                message = sys.argv[3]
            else:
                message = sys.argv[2]
        
        if not message:
            print("Error: Commit message is required")
            return
            
        commit_changes(message)
    
    elif command == "log":
        if len(sys.argv) >= 3 and sys.argv[2] == "--all":
            show_all_logs()
        else:
            show_log()
    
    elif command == "status":
        show_status()
    
    elif command == "branch":
        if len(sys.argv) < 3:
            list_branches()
            return
            
        branch_name = sys.argv[2]
        create_branch(branch_name)
    
    elif command == "branches":
        list_branches()
    
    elif command == "checkout":
        if len(sys.argv) < 3:
            print("Error: Branch name is required")
            return
            
        if sys.argv[2] == "-b":
            if len(sys.argv) < 4:
                print("Error: Branch name is required after -b flag")
                return
                
            branch_name = sys.argv[3]
            checkout_branch(branch_name, create=True)
        else:
            branch_name = sys.argv[2]
            checkout_branch(branch_name)
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: Commit hash is required")
            return
            
        commit_hash = sys.argv[2]
        restore_commit(commit_hash)
    
    elif command == "clean":
        force = len(sys.argv) >= 3 and sys.argv[2] == "-f"
        clean_untracked_files(force=force)
    
    elif command == "rm":
        if len(sys.argv) < 3:
            print("Error: File path is required")
            return
            
        file_path = sys.argv[2]
        force = "-f" in sys.argv
        remove_file(file_path, force=force)

    elif command == "rebase":
        if len(sys.argv) < 3:
            print("Error: Target branch name is required")
            return
                
        target_branch = sys.argv[2]
        rebase_branch(target_branch)
    
    else:
        print(f"Unknown command: {command}")



if __name__ == "__main__":
    main()
