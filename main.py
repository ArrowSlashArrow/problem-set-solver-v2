import os, sys, subprocess, time  # theres no way these every fail to import
log_file = ".log"
class Event:
    def __init__(self, name="UNKNOWN EVENT", **kwargs):
        self.values = kwargs
        divider = " | " if len(kwargs) > 0 else ""
        open(log_file, "a").write(f"[{time.time():.3f} {name.upper()}{divider}{str(self.values)[1:-1]}]\n")

restart_enabled = False if "--no-restart" in sys.argv else True
no_exit_text = True if "--no-exit-text" in sys.argv else False

if log_file not in os.listdir():
    open(log_file, "w").close()
elif not "--restarting" in sys.argv:
    open(log_file, "a").write("\n")
    Event("START PROGRAM")

def restart(updating=False):
    if not restart_enabled:
        if not updating:
            print("Restart is disabled")
        return
    Event("RESTART", REASON="UPDATING" if updating else "USER RESTART")
    print("Restarting script...")
    args = [sys.executable, __file__] + sys.argv
    if updating:
        args.append("--no-restart")
    subprocess.run(args + ["--no-exit-text", "--restarting"])

install_str = f"{sys.executable} -m pip install --upgrade --force-reinstall --break-system-packages -r requirements.txt"
# todo alternating colours
try:
    import importlib.util, json, easygui, shutil, requests, hashlib
    from rich import console, table, prompt, text, traceback
except ModuleNotFoundError as e:
    try:
        Event("installing dependencies")
        print("Installing required modules...")
        subprocess.check_call(install_str.split(" "))
        print("Restarting the script...")
        if os.name == "posix":
            print("tkinter might not be installed. Run one of these commands depending on your distro:")
            print(" - Ubuntu/Debian: sudo apt install python3-tk\n - Fedora: sudo dnf install python3-tkinter\n - Arch: sudo pacman -S tk")
            quit()
        else:
            restart()
    except Exception as e:
        print(f"\x1b[38;5;9mFATAL\x1b[0m] \x1b[38;5;9mCould not install the required libraries. please run '{install_str}'\n Error: {e}\x1b[0m")
    

# nicer way of storing modules
# also python law dictates that every main.py must have at least one struct
class Module:
    def __init__(self, filename: str, name: str, description: str, tags: list[str], version: int):
        self.name = name
        self.description = description
        self.tags = tags
        self.filename = filename
        self.version = version

    # pretty-print metadata dict
    def __str__(self):
        md_dict = {}
        md_dict["name"] = self.name
        md_dict["description"] = self.description
        md_dict["tags"] = self.tags
        md_dict["filename"] = self.filename
        md_dict["version"] = self.version

        return json.dumps(md_dict, indent=4)
    
    # nicely-formatted string
    def get_str(self):
        return f"[green]{self.name}[/green] ([yellow]{self.filename}[/yellow])"
    
# settings struct for convenience
class Setting:
    def __init__(self, name, type, value, description):
        self.type = type
        self.value = value
        self.name = name
        self.description = description


# unpack function for list[Module] -> good data for new_table() 
# returns [[ids], [name], [descriptions], [tags as a string]]
def get_module_data(modules: list[Module]):
    ids = []
    names = []
    descriptions = []
    tags = [] 
    versions = []
    filenames = []
    for m in modules:  # formats everything properly so rich can display it
        ids.append(str(len(ids)))
        names.append(m.name)
        descriptions.append(m.description)
        tags.append(", ".join(m.tags))
        versions.append(str(m.version))
        filenames.append(m.filename)
    return [ids, names, descriptions, tags, versions, filenames]

# intialize rich console and module table arrays
console = console.Console()
modules = []

info = {
    "authors": ["Authors: ", "</> (arrow) and bitfeller"],
    "version": ["Version: ", "1.1.1"],
    "last_updated": ["Last updated on: ", "2025/04/16"]
}

about_txt = "\n".join(f" - {value[0]}{value[1]}" for value in info.values())

# user guide
tutorial_str = text.Text.from_markup(f"""\n-------------------------------[ [green]BEGIN TUTORIAL[/] ]------------------------------- 
Welcome to the problem set solver tutorial!

[bold]## USAGE[/]
To select an action, type its [yellow]name[/] or its corresponding [green]ID[/].

To get started, download a module from the server by typing 7.
Once at the module selection screen, you can select modules by name or number. To install mutiple modules, type their corresponding numbers or names separated by spaces (e.g. 1, 2, 3)
You can now run these modules by typing 0 at the action selection, and selecting the module you want to run. You can only select one module to run at a time.
If a module crashes, an error will appear displaying the crash message.

If you want to delete all modules, type 'all' or 'everything' at the module delete prompt.
Similarly, if you want to download all modules on the server, type 'all' or 'everything' at its respective prompt.

If you want to go back to the action selection from any prompt, type [cyan]back[/].
If you want to send feedback or suggest a feature, select action 12 and enter the feedback.

[bold]## COMMON PROBLEMS[/]
If you can't see any modules, they might still be downloading from the server, or your tag search is filtering them out.
To change the tag search, go to the settings changer by typing 10 and follow the instructions.

[bold]## MODULES[/]
To create a module, you must know how to write basic code in python, and if you want to work with complex equations, learn how to use SymPy.
Your modules should not contain any dependencies or import other than utils.
If you don't know how to write code, you can contact me to make it at @arrowslasharrow on Discord.

Made by {info['authors'][1]} on 2025/03/19, last updated on v{info['version'][1]} at {info['last_updated'][1]}
--------------------------------[ [red]END TUTORIAL[/] ]--------------------------------
""")

about_str = text.Text.from_markup(f"""\nAbout Problem Set Solver:\n{about_txt}""")

# shorthand
actions = {
    "Select a module": "sel",
    "List all modules": "ls",
    "Update a module": "upd",
    "Update all modules": "updall",
    "Create a new module": "touch",
    "Remove a module": "rem",
    "Import module from file": "fimport",
    "Import module from server": "simport",
    "Export module to server": "ex",
    "Display all modules on server": "sls",
    "Open admin panel": "oap",
    "Change settings": "set",
    "Update the script": "upd",
    "Print user guide": "guide",
    "Send feedback": "sfb",
    "About": "about",
    "Restart": "r",
    "Exit": "x"
}

update_files = [
    # "main.py",
    "utils.py",
    "requirements.txt",
    "README.md",
    "admin_enc"
]

# name, desc, tags, version, 
boilerplate = """# name: <NAME>
# description: <DESC>
# tags: <TAGS>
# version: 1
# made by <USER> on <DATE>
import math, sympy
from utils import *

def solver():
    pass
"""

# module table
module_table_columns = {
    "ID": {"style": "cyan", "justify": "right"},
    "Module Name": {"style": "green", "justify": "left"},
    "Module Description": {"style": "yellow", "justify": "left"},
    "Tags": {"style": "red", "justify": "left"},
    "Version": {"style": "purple", "justify": "right"},
    "Filename": {"style": "grey62", "justify": "right"}
}

settings_table_columns = {
    "ID": {"style": "cyan", "justify": "right"},
    "Setting": {"style": "green", "justify": "left"},
    "Value": {"style": "yellow", "justify": "left"},
    "Description": {"style": "red", "justify": "left"},
    "Data Type": {"style": "purple", "justify": "left"},
}

# settings
settings = {}

# tracebacks
def display_traceback():
    if settings["display_tracebacks"].value:
        console.print(traceback.Traceback())


# wanted to refactor this but couldn't
# if it works, don't touch it
def pack_dicts(*args):
    keys = [list(arg.keys()) for arg in args]
    if len(set(map(tuple, keys))) != 1:
        return args[0]
    keys = keys[0]
    values = [list(arg.values()) for arg in args]
    vals = list(map(list, zip(*values[::-1])))
    return {k: v for k, v in zip(keys, vals)}


def transpose(array):
    return [list(m) for m in zip(*array)]


# update the various settings arrays
def update_settings():
    global settings, setting_data
    raw_settings = json.load(open("settings.json", "r"))
    for key in list(raw_settings.keys()):
        settings[key] = (Setting(key, *raw_settings[key][0:3]))


# parse num util function
def parse_num(num: str):
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return num


# return rich table object
# example title: {"fone linging": {"style": "cyan", "align": "left"}, ...}
# example rows: [["data", "data", "data"], ...]
def new_table(name: str, columns: dict, rows: list[list]):
    module_table = table.Table(title=name)
    if "striped_rows" in settings and settings["striped_rows"].value:
        module_table.row_styles=["on grey11", "on grey15"]

    for title, formatting in columns.items():
        module_table.add_column(title, justify=formatting["justify"], style=formatting["style"])
    for vals in zip(*rows):
        module_table.add_row(*vals)
    return module_table


def get_valid_input(input_message: str, valid_inputs: list[str], indices: bool=False, back_enabled : bool=True, err_word: str="input", many=False, everything=False):
    original_inputs = valid_inputs[:]
    valid_inputs.extend([str(i) for i in range(len(valid_inputs))] if indices else [])    
    if not many:
        choice = ""
        while True:
            inp = prompt.Prompt.ask(input_message).lower().rstrip().lstrip()
            if inp == "back" and back_enabled:
                choice = "\0"
                break
            
            if inp not in valid_inputs:
                console.print(f"{inp} is not a valid {err_word}, please try again.")
                continue
            
            if indices and type(parse_num(inp)) == int:
                choice = valid_inputs[int(inp)]
                break
            else:
                choice = inp
                break
        return choice
    else:
        choices = []
        inp = [i.lstrip().rstrip() for i in prompt.Prompt.ask(input_message).split(",")]
        if inp[0].lower() in ["all", "everything"] and everything:
            return original_inputs
        for i in inp:
            # skip over the input if it is invalid
            if i not in valid_inputs:
                continue

            if indices and type(parse_num(i)) == int:
                choices.append(valid_inputs[int(i)])
            else:
                choices.append(i)
        return choices


def get_metadata(file: str, raw_str=False):
    current_module = Module("file", "<Unknown>", "<No description>", [], "<Unknown>")
    ignore = False
    raw_data = open(file, "r").read() if not raw_str else file

    lines = raw_data.split("\n")
    for line in lines:
        if "# name: " in line:
            current_module.name = line.split("# name: ")[1]
        if "# description: " in line:
            current_module.description = line.split("# description: ")[1]
        if "# tags: " in line:  
            current_module.tags = line.split("# tags: ")[1].split(", ")
        if "# version: " in line:
            current_module.version = int(line.split("# version: ")[1])
        if settings["ignore_str"].value in line.lower():
            ignore = True
    return current_module if not ignore else "IGNORE"


def refresh_modules(loaded_text=False):
    global modules
    Event("refreshed mods")
    module_files = [m for m in os.listdir("modules") if m.endswith(".py") and os.path.isfile(f"modules/{m}")]

    modules = []
    # populate arrays from /modules
    for m in range(len(module_files)):
        # get metadata from within file
        current_module = Module("file", "<Unknown>", "<No description>", [], "<Unknown>")

        try:
            meta = get_metadata(f"modules/{module_files[m]}")
            if meta == "IGNORE":
                continue
            current_module = meta
        except FileNotFoundError:
            console.print(f"[red]Could not access {module_files[m]}: Not found in /modules [/]")
        except PermissionError:
            console.print(f"[red]Could not access {module_files[m]}: Permission denied[/]")
        except Exception as e:
            console.print(f"[red]Couldnt read {module_files[m]} becuase {e}[/]")

        # get the rest of metadata
        current_module.filename = module_files[m]
       
        modules.append(current_module)
    
    if len(modules) > 0 and loaded_text:
        mods = len(modules)
        console.print(f"[green]Loaded {mods} module{'s' if mods != 1 else ''} successfully[/]")


def update_module_table():
    global module_table, module_table_data
    refresh_modules()

    filters = [tag.lstrip().rstrip() for tag in settings["filter_tags"].value.split(",")]
    # gets rid of empty strings
    for filter in filters:
        if filter == "":
            filters.remove(filter)
    filtered_modules = []
    for module in modules:
        # if module tags are within the filter constraints, add the module to the table
        if set(filters) <= set(module.tags):
            filtered_modules.append(module)
    module_table_data = get_module_data(filtered_modules)
    module_table = new_table("Installed Modules", module_table_columns, module_table_data)


# returns module filename
def module_select(other_valid_inputs=[]):
   
    # update table at execution time to account for imported modules
    update_module_table()
    # info messages
    if len(settings['filter_tags'].value) > 0:
        console.print(f"Searching by these tags: {', '.join(settings['filter_tags'].value)}")
    console.print("If no modules show up, type 'back' and try again in a few seconds, or check your tags setting.")
    console.print(module_table)

    # get module
    module_names = [m.name for m in modules]
    module_names.extend(other_valid_inputs)
    choice = get_valid_input(f"> Select a module by [cyan]ID[/] or [green]name[/]", module_names, True, "module")
    if choice == "\0":  
        return
    if choice in other_valid_inputs:
        return choice
    # map choice index to module
    choice_index = module_names.index(choice)
    mod = modules[choice_index]
    Event("module choice", MODULE=mod.filename)
    return mod


def action_select():
    shorthand = list(actions.values())
    full_actions = list(actions.keys())
    lower_actions = [a.lower() for a in full_actions]

    ids = [str(i) for i in range(len(actions))]
    titles = {
        "ID": {"style": "green", "justify": "right"},
        "Action": {"style": "yellow", "justify": "left"}
    }
    action_table_data = [ids, full_actions]
    if settings["shorthand_actions"].value:
        titles["Shorthand"] = {"style": "red", "justify": "left"}
        action_table_data.append(shorthand)

    action_table = new_table("Actions", titles, action_table_data)
    console.print(action_table)
    available_actions = lower_actions[:]
    available_actions.extend(shorthand)
    choice = get_valid_input(f"> Select an action by its [green]ID[/] or [yellow]name[/]{f' or [red]shorthand[/]' if settings['shorthand_actions'].value else ''}", available_actions, indices=True, err_word="action")
    
    if choice in shorthand:
        choice = full_actions[shorthand.index(choice)]
    elif choice in lower_actions:
        choice = full_actions[lower_actions.index(choice)]
    Event("ACTION", ACTION=choice)
    return choice
        

def check_module(path: str):
    # load module
    spec = importlib.util.spec_from_file_location(path, path)
    external_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external_module)

    # check if module has solver() function
    if hasattr(external_module, "solver"):
        return external_module
    else:
        return None


def load_module(module: Module):
    module_obj = check_module(f"modules/{module.filename}")
    Event("START MODULE", MODULE=module.filename)
    if module_obj:
        try:
            module_obj.solver()
            Event("END MODULE", STATUS="OK")
        except Exception as e:
            Event("END MODULE", STATUS="CRASH")
            display_traceback()
            console.print(f"[red]{module.name} crashed :([/]")
    else:
        Event("END MODULE", STATUS="NO SOLVER")
        console.print(f"\n[yellow]{module.name} does not have a solver() function. Unable to run module.[/]\n")


def boolstr(s: str):
    return 


def format_settings(settings: list[Setting]):
    raw_settings = {}
    for setting in list(settings.values()):
        raw_settings[setting.name] = [setting.type, setting.value, setting.description]
    return raw_settings


def change_settings():
    # initialize table and columns
    
    settings_table_data = []
    # populate settings table
    index = 0
    for setting in list(settings.values()):
        name = setting.name
        value = str(setting.value)
        data_type = setting.type
        description = setting.description
        settings_table_data.append([str(index), name, value, description, data_type])
        index += 1

    settings_table = new_table("Settings", settings_table_columns, transpose(settings_table_data))

    console.print(settings_table)
    choice = get_valid_input(f"> Select the setting you want to change by its [cyan]ID[/] or [green]name[/]", list(settings.keys()), True, err_word="setting")
    if choice == "\0":
        return
    
    inp = prompt.Prompt.ask(f"Enter the new value for {choice}")
    
    # format input according to data type
    match settings[choice].type:
        case "boolean":
            inp = inp.lower() in ("true", "yes", "ye", "1", "y", "yep", "yea", "yeah")
        case "positive number":
            parsed = parse_num(inp)
            if type(parsed) not in [float, int]:
                console.print(f"[yellow] Unable to set {choice} to {inp}, the new value should be a positive number[/]")
                return
            if abs(parsed) != parsed and parsed != 0:
                console.print(f"[yellow] Unable to set {choice} to {inp}, the new value must be positive.[/]")
                return
            inp = parsed 

    # change and save setting
    Event("SETTING CHANGE", SETTING=choice, VALUE=inp)
    settings[choice].value = inp
    Event("SAVED SETTINGS")
    json.dump(format_settings(settings), open("settings.json", "w"), indent=4)


def local_file_select():
    # get file
    try:
        selected_file = easygui.fileopenbox()
        if not selected_file:
            return
        filename = selected_file.split("/")[-1]
    except Exception as e:
        console.print("Unable to open file dialog")
        return  # todo: file select through path
    
    # filter out bad input
    if not filename.endswith(".py"):
        console.print("[red]Invalid input file. Please select a .py file.[/]")
        return
    
    # check if it is already in the modules directory
    if filename in os.listdir("modules"):
        choice = get_bool(f"{filename} is already in the modules directory. Do you want to replace it?")
        if not choice:
            return
    
    # check for solver function
    if not check_module(filename):
        console.print(f"[yellow]{selected_file} does not have a solver() function. It cannot be ran as a module and will not be imported.[/yellow]")
        Event("LOAD LOCAL MODULE", STATUS="NO SOLVER")

    try:  # copy file to modules/ directory
        shutil.copy(selected_file, "modules")
        console.print(f"[green]Loaded {filename} successfully[/]")
        Event("LOAD LOCAL MODULE", STATUS="OK")
    except Exception as e:
        console.print(f"[red]Could not read {selected_file} because {e}[/]")
        Event("LOAD LOCAL MODULE", STATUS="FAILED", REASON=e)


def delete_module():
    all = ["all", "everything"]
    module = module_select(other_valid_inputs=all)
    if not module:
        return
    
    if module in all:
        if not get_bool(f"[[bright_red]WARNING[/]] [red]This action is irreversible. Are you absolutely sure you want to delete every single module you have installed?[/]"):
            return
        
        try:
            for file in [f for f in os.listdir("modules") if f != "utils.py"]:
                os.remove(f"modules/{file}")
            Event("DELETED ALL MODULES", STATUS="OK")
        except Exception as e:
            Event("DELETED ALL MODULES", STATUS="FAILED", REASON=e)
    else:
        if settings["confirm_delete"].value:
            if not get_bool(f"Are you sure you want to delete {module.name} ({module.filename})?"):
                return
        os.remove(f"modules/{module.filename}")
        Event(f"DELETED {module.filename}")


def create_module():
    filename = prompt.Prompt.ask("> Enter the filename of the new module")
    if filename == "back":
        return
    if filename.endswith(".py"):
        filename = filename[:-3]  # remove .py
    content = boilerplate

    name = prompt.Prompt.ask("> Enter the name of the module")
    description = prompt.Prompt.ask("> Enter the description for this module")
    tags = ", ".join(sorted(list(set([t.rstrip().lstrip() for t in prompt.Prompt.ask("> Enter tags separated by commas").split(",") if t]))))
    user = prompt.Prompt.ask("> Enter your username")
    date = time.strftime("%Y/%m/%d", time.localtime())

    # put all the data into the boilerplate
    content = content.replace("<USER>", user)
    content = content.replace("<NAME>", name)
    content = content.replace("<DESC>", description)
    content = content.replace("<TAGS>", tags)
    content = content.replace("<DATE>", date)

    try:
        with open(f"modules/{filename}.py", "w") as f:
            f.write(content)

        console.print(f"[green]successfully created {filename}.py[/]")
        Event(f"CREATED {filename}.py", STATUS="OK")
    except Exception as e:
        console.print(f"[red]could not create {filename}.py[/]")
        Event(f"CREATED {filename}.py", STATUS="FAILED", REASON=e)

# todo: finish pasting all the events everywhere
## SERVER STUFF ##
session = None
online = False
last_ping = 0
server = ""
server_str = ""

headers = {
    "Content-Type": "application/json"
}

def get_bool(msg):
    return prompt.Confirm.ask(msg)


def get_server_pw():
    pw = settings["server_pw"].value
    if len(pw) <= 0: 
        pw = prompt.Prompt.ask("Enter password for server")
    return pw


def server_required(func):
    def wrapper(*args, **kwargs):
        global session
        # check if server is online
        if not online and not reconnect():
            return

        # assumes server is online
        if not session:
            session = get_session()
            if not session:
                return
        return func(*args, **kwargs)
    return wrapper


@server_required
def format_payload(payload: str, modules=[], feedback="", pwd=""):
    global session
    ready_payload = {
        "action": payload
    }

    match payload:
        case "list" | "exit":
            ready_payload["session"] = session
        case "install" | "version" | "metadata":
            ready_payload["session"] = session
            ready_payload["mod"] = [m.name for m in modules]
        case "upload":
            ready_payload["session"] = session
            m = module_select()
            if not m:
                return "\0"
            selected_module = m.filename 
            ready_payload["data"] = open(f"modules/{selected_module}", "r").read()
            ready_payload["filename"] = selected_module
            ready_payload["mod"] = m.name
            ready_payload["overrideVersion"] = False
            ready_payload["overrideMod"] = True
            ready_payload["session"] = session
        case "feedback":
            ready_payload["session"] = session
            ready_payload["feedback"] = feedback
        case "log":
            Event("SESSION", SESSION=session)
            ready_payload["log"] = open(".log", "r").read().split("\n\n")[-1]
        case "admin script":
            ready_payload["pwd"] = pwd
        case _:
            pass

    if settings["show_requests"].value:
        console.print(text.Text.from_markup("[[yellow]PAYLOAD[/]]") + text.Text(str(ready_payload)))
    
    return ready_payload


def show_response(req):
    if settings["show_requests"].value:
        colour = "[red]" if json.loads(req.text)["success"] == 0 else "[green]"
        console.print(text.Text.from_markup(f"[{colour}RESPONSE[/]]") + text.Text(str(req.text)))


def send_request(payload, raw=False):
    payload_arg = payload if "log" not in payload else "LOG FILE"
    Event(f"SENDING PAYLOAD TO {server_str}", PAYLOAD=payload_arg)
    req = requests.post(server, json=payload, headers=headers, timeout=settings["request_waittime"].value)
    if raw and settings["show_requests"].value:
        console.print(text.Text.from_markup("[[yellow]PAYLOAD[/]]") + text.Text(str(payload)))
    Event(f"RESPONSE FROM {server_str}", CODE=req.status_code, RESPONSE=req.text)
    show_response(req)
    if json.loads(req.text)["data"] == "easter egg":
        print(r"easter egg triggered lmao goodbye (this is a 0.1% chance)")
        raise KeyboardInterrupt
    return req


# returns true if server is online
def test_ping():
    global last_ping
    try:
        req = send_request({"action": "ping"}, raw=True)
        last_ping = time.time()
        # display appropriate message according ot stateus code
        match req.status_code:
            case 200:
                console.print(f"[green]Server {server_str} is online[/] (latency: {int(req.elapsed.seconds * 500 + req.elapsed.microseconds / 2000)}ms)")
                console.print(f"Message from server: {json.loads(req.text)['data']}")
                Event("PINGED SERVER", STATUS="ONLINE")
                return True
            case 523:
                console.print(f"[red]Server {server_str} is offline[/]")
                Event("PINGED SERVER", STATUS="OFFLINE")
            case 504:
                console.print("[red]Gateway Timeout (504). Server is offline[/]")
                Event("PINGED SERVER", STATUS="TIMEOUT")
            case 500:
                console.print("[yellow]Server is updating (500). Server is offline[/]")
                Event("PINGED SERVER", STATUS="UPDATING")
            case _:
                console.print(f"[red]Unknown error: {req.status_code}[/]")
                Event("PINGED SERVER", STATUS=req.status_code)
    except json.decoder.JSONDecodeError:
        console.print("[red]Server responded with bad JSON, and is likely down.[/]")
        Event("PINGED SERVER", STATUS="BAD JSON")
    except Exception as e:
        console.print(f"[red]Could not connect to the server for this reason: {e} [/]") 
        Event("PINGED SERVER", STATUS="FAILED", REASON={e})   
    return False


def get_session():
    req = send_request({"action": "session", "pwd": get_server_pw()}, raw=True)

    # parse response
    success = json.loads(req.text)["success"]
    data = json.loads(req.text)["data"]

    if success == 0:
        if data == "bad pwd":
            console.print(f"Invalid password; unable to generate session. If the [yellow]server_pw[/] value is set, it might be set to the wrong password. ")
        return
    session = data
    Event("GENERATED SESSION")
    return session


def reconnect():
    if last_ping + settings["reconnect_timeout"].value < time.time():
        console.print("[red]Server is offline. Unable to perform action.[/]")
    else:
        Event("RECONNECT ATTEMPT")
        console.print("[red]Server is offline.[/][yellow] Attempting to reconnect...[/]")
        online = test_ping()
        if online:
            return True
    return False


@server_required
def list_server_modules():
    global session
    # send payload
    payload = format_payload("list")
    req = send_request(payload)

    response = json.loads(req.text)
    if response["success"] == 0:
        if response['data'] == 'bad session':
            session = get_session()
        console.print(f"[red]Could not list modules.[/]")
        return

    if len(response['data']) == 0:
        console.print("No modules in here")
        return
    
    modules = []
    for name, meta in response["data"].items():
        new_mod = Module("file", "<Unknown>", "<No description>", [], "<Unknown>")
        new_mod.name = name
        new_mod.description = meta["desc"]
        new_mod.version = meta["version"]
        new_mod.filename = meta["filename"]
        new_mod.tags = meta["tags"]
        modules.append(new_mod)
    
    server_module_table = new_table(f"Modules on {server_str}", columns=module_table_columns, rows=get_module_data(modules[:]))
    console.print(server_module_table)

    return modules


@server_required
def server_module_select():
    available_modules = list_server_modules()
    selected_modules = get_valid_input(f"> Select module(s) by [cyan]ID[/] or [green]name[/] (separated by commas if there are multiple)", available_modules, True, "module", many=True, everything=True)
    if selected_modules == "\0":
        return

    Event(f"REQUESTING MODULES FROM {server_str}", MODULES=[m.filename for m in selected_modules])
    payload = format_payload("install", modules=selected_modules)
    mod_req = send_request(payload)
    mod_resp = json.loads(mod_req.text)["data"]
    for mod in mod_resp:  # mod: [metadata dict, contents]
        meta = mod["meta"]
        data = mod["data"]
        filename = ""
        name = ""
        try:
            filename = meta["filename"]
            name = meta["name"]
        except Exception as e:
            console.print(f"[yellow]WARNING: Srever sent malformed metadata, using default values.[/]")
            temp = "mod_" + str(int(time.time())) 
            filename = f"{temp}.py"
            name = temp

        if filename in os.listdir("modules"):
            choice = get_bool(f"[green]{name}[/] ([yellow]{filename}[/]) is already in the modules directory. Do you want to replace it?")
            if not choice:
                continue
        try:
            with open(f"modules/{filename}", "w") as m:
                m.write(data)
                Event(f"DOWNLOADED {filename}", STATUS="OK")
        except PermissionError:
            console.print(f"[red]Unable to install {name} because permission was denied. Make sure that this folder is not read-only. [/]")
            Event(f"DOWNLOADED {filename}", STATUS=e)
        except Exception as e:
            console.print(f"[red]Unable to install {name} because of {e}[/]")
            Event(f"DOWNLOADED {filename}", STATUS=e)


@server_required
def upload_module():
    payload = format_payload("upload")
    if payload == "\0":
        return
    req = send_request(payload)
    if json.loads(req.text)["success"]:
        console.print("[green]Module uploaded successfully.[/]")
        Event("UPLOADED MODULE", STATUS="OK")
    else:
        console.print("[red]Module upload failed[/]")
        Event("UPLOADED MODULE", STATUS="FAILED")

@server_required
def update_module(module=""):
    if module == "":
        module = module_select()
        if not module: 
            return

    filename = f'modules/{module.filename}'
    # make backup
    shutil.copyfile(filename, f'{filename}.bak')
    Event("CREATED BACKUP", FILE=filename)
    
    req = send_request(format_payload("version", [module]))
    if json.loads(req.text)["success"] == 1:
        version = int(json.loads(req.text)["data"][0])
        module_version = int(module.version) if type(parse_num(module.version)) == int else -1

        if module_version < version:
            payload = format_payload("install", modules=[module])
            req = send_request(payload)
            mod = json.loads(req.text)["data"][0]
            
            with open(filename, "w") as m:
                m.write(mod[1])    
            console.print(f"[green]Updated {module.get_str()}[/]")
            Event("UPDATED MODULE", STATUS="OK")
        else:
            console.print(f"[green]{module.get_str()} is already up to date.[/]")
            Event("UPDATED MODULE", STATUS="ALREADY UPDATED")
    else:
        match json.loads(req.text)["data"]:
            case "no mod":
                console.print(f"[red]Unable to update {module.get_str()} because it is not on the server.[/]")
                Event("UPDATED MODULE", STATUS="NOT ON SERVER")
            case _:
                console.print(f"[red]Unable to update {module.get_str()}[/]")
                Event("UPDATED MODULE", STATUS="FAILED")
        shutil.copyfile(f'{filename}.bak', filename)
        Event("REVERT TO BACKUP", FILE=filename)

    Event("DELETED BACKUP", FILE=filename)
    os.remove(f'{filename}.bak')
            


def update_all(status_text=False):
    refresh_modules(loaded_text=status_text)
    for m in modules:
        update_module(m)


@server_required
def send_feedback():
    feedback = input("> What feedback would you like to share with us?\n> ")
    if feedback == "\0":
        return
    try:
        # loads request as dict
        req = json.loads(send_request(format_payload("feedback", feedback=feedback)).text)
        if req["success"] == 1:
            console.print("[green]Thanks for your feedback :)[/]")
            Event("SENT FEEDBACK", STATUS="OK", FEEDBACK=feedback)
            return
    except Exception as e:
        console.print(f"[red]error: {e}[/]")
        Event("SENT FEEDBACK", STATUS="FAILED", REASON=e)
    # print this if bad params or crash 
    console.print("[red]Unable to send feedback :([/]")


def update_self():
    with console.status("Updating files...", spinner="dots12"):
        for file in update_files:
            # make backup
            if file in os.listdir():
                shutil.copyfile(file, f'{file}.bak')
            else:
                open(f"{file}.bak", "w").close()
            req = requests.get(f"https://raw.githubusercontent.com/ArrowSlashArrow/problem-set-solver-v2/refs/heads/main/{file}")
            # get file
            if req.status_code == 404:
                console.print(f"[red]Could not download {file} because it was not found in the repo.[/]")
                Event("FILE DOWNLOAD", FILE=file, STATUS="NOT FOUND")
                os.remove(f'{file}.bak')
            elif req.status_code != 200:
                console.print(f"[red]Could not download {file} ({req.status_code}).[/]")
                Event("FILE DOWNLOAD", FILE=file, STATUS="NOT FOUND")
                os.remove(f'{file}.bak')
            else:
                console.print(f"[green]Successfully downloaded {file}... [/]", end="")
                Event("FILE DOWNLOAD", FILE=file, STATUS="OK")
                # write to file
                try:
                    open(file, "w", encoding="utf-8").write(req.text)
                    console.print(f"[green]Successfully updated {file} :)[/]")
                    Event("FILE WRITE", FILE=file, STATUS="OK")
                except Exception as e:
                    console.print(f"[red]Could not write to {file} because {e}[/]\n[yellow]Reverting to old copy of {file}...[/]")
                    shutil.copyfile(f'{file}.bak', file)
                    Event("FILE WRITE", FILE=file, STATUS="FAILED", REASON=e)
                finally:
                    os.remove(f'{file}.bak')


def xor_encrypt(text: bytes, pwd: str):
    pwd_encoded = pwd.encode()
    return bytes([byte ^ pwd_encoded[index % len(pwd_encoded)] for index, byte in enumerate(text)])


def open_admin_script(pwd):
    if "admin_enc" not in os.listdir():
        console.print("[yellow]There is no `admin_enc` file in the directory. Please redownload it from the repo.[/]")
        return
    try:
        # decrypt the file
        f = open("admin_enc", "rb").read()
        open("admin.py", "wb").write(xor_encrypt(f, pwd))
        Event("DECRYPTED ADMIN PANEL", STATUS="OK")
    except Exception as e:
        display_traceback()
        console.print("[red]Failed to decrypt the admin panel[/]")
        Event("DECRYPTED ADMIN PANEL", STATUS="FAILED")
        return

    try:
        import admin  # type:ignore
        admin.main()
        Event("RAN ADMIN PANEL", STATUS="OK")
    except:
        console.print("[red]Admin panel crashed[/]")
        Event("RAN ADMIN PANEL", STATUS="FAILED")
    
    # delete the temp file
    os.remove("admin.py")
    Event("DELETED DECRYPTED ADMIN PANEL")


def action_controller(action: str):
    match action:
        case "Select a module":
            module = module_select()
            if not module:
                return
            console.print(f"\n-----------[ [green]Start of {module.name} [/]]-----------")
            try:
                load_module(module)
            except KeyboardInterrupt:
                print()
                Event("END MODULE", STATUS="OK")
            console.print(f"------------[ [red]End of {module.name} [/]]------------\n")
        case "List all modules":
            update_module_table()
            console.print(module_table)
        case "Import module from file":
            local_file_select()
        case "Import module from server":
            server_module_select()
        case "Export module to server":
            upload_module()
        case "Update a module":
            update_module()
        case "Update all modules":
            update_all()
        case "Create a new module":
            create_module()
        case "Remove a module":
            delete_module()
        case "Display all modules on server":
            list_server_modules()
        case "Change settings":
            change_settings()
        case "Update the script":
            try:
                update_self()
            except Exception as e:
                display_traceback()
                console.print(f"[red]could not update the script.[/]")
        case "Print user guide":
            console.print(tutorial_str)
        case "Send feedback":
            send_feedback()
        case "Restart":
            restart()
        case "Exit":
            print("Exiting...")
            send_request(format_payload("log"))
            send_request(format_payload("exit")) if session else 0
            raise KeyboardInterrupt
        case "Open admin panel":
            # check that user can access it
            pwd = prompt.Prompt.ask("> Enter password to access the admin panel", password=True)
            if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == "878248de86cb7e6492aae17cddff64c393ca018c872ced068e846737e7ec7448":
                Event("OPENED ADMIN PANEL", STATUS="GOOD PASSWORD")
                open_admin_script(pwd)
            else:
                Event("OPENED ADMIN PANEL", STATUS="BAD PASSWORD")
                console.print("[red]Incorrect password.[/]")

        case "About":
            print(about_str)


def preload():
    global online, server, server_str
    os.system("cls" if os.name == "nt" else "clear")

    # create /modules if it does not exist
    # for some FUCKING reason, there is not way to make this folder NOT read-only. what is the deal with this?
    # it turns out every single file on my system is a read-only file (including c:/windows). wtf?
    if not os.path.exists("modules"):
        os.mkdir("modules")

    try:
        with console.status("Loading...", spinner="dots12"):
            # load settings
            update_settings()
        console.print("[green]Loaded settings successfully[/]")
        Event("LOADED SETTINGS", STATUS="OK")
    except Exception as e:
        console.print("[red]FATAL: Could not load settings[/]")
        Event("LOADED SETTINGS", STATUS="FAILED", REASON=e)
        raise KeyboardInterrupt

    with console.status("Testing server connection...", spinner="earth"):
        # ping server and check connection
        server = f"https://{settings['module_server'].value}/"
        server_str = f"{server}" if settings['censor_server'].value else '[SERVER]'
        online = test_ping()

    print()
    installed_modules = [f for f in os.listdir("modules") if f != "utils.py" and f.endswith(".py")]
    # autoupdate
    try:
        if settings["autoupdate_modules"].value and len(installed_modules) > 0:
            updating = len(installed_modules)
            with console.status(f"\nUpdating {updating} module{'s' if updating != 1 else ''}...", spinner="bouncingBar"):
                update_all(status_text=True)
            Event("MODULE AUTOUPDATE", STATUS="OK")
    except Exception as e:
        console.print(f"[red]Could not update modules.[/]")
        Event("MODULE AUTOUPDATE", STATUS="FAILED", REASON=e)
    
    try:
        if settings["autoupdate_script"].value:
            print()
            with console.status(f"\nUpdating the script...", spinner="bouncingBar"):
                update_self()
                Event("UPDATED SCRIPT", STATUS="OK")
                restart(updating=True)
    except Exception as e:
        console.print(f"[red]Could not update the script ({e})[/]")
        Event("UPDATED SCRIPT", STATUS="FAILED", REASON=e)
    console.print(tutorial_str)


def main():
    preload()
    Event("PRELOAD COMPLETE")

    # sample code for the admin panel
    # enc_file = "06-0a-14-44-08-13-05-07-46-4c-1a-79-50-59-57-41-02-17-0b-01-06-4c-47-1a-09-05-02-0a-0c-53-07-16-05-0d-16-44-40-46".split("-")
    # open("admin_enc", "w").write("".join([chr(int(n, 16)) for n in enc_file]))
    
    while True:
        action_controller(action_select())
        update_settings()



try:
    if __name__ == "__main__":
        main()
except KeyboardInterrupt:
    if not no_exit_text:
        print("\nThanks for using Problem Set Solver by </> (arrow) and bitfeller!\nExiting...")  
    Event("END PROGRAM", STATUS="OK")
    sys.exit(0)
except Exception as e:
    display_traceback()
    print(f"Script crashed\nExiting...")
    Event("END PROGRAM", STATUS="CRASH", REASON=e)