import os, importlib.util, json, easygui, shutil, copy, time, requests
from rich import console, table, prompt

# nicer way of storing modules
# also python law dictates that every main.py must have at least one struct
class Module:
    def __init__(self, filename: str, name: str, description: str, tags: list[str], version: int, id: int | None=-1):
        self.name = name
        self.description = description
        self.tags = tags
        self.id = id
        self.filename = filename
        self.version = version

    def __str__(self):
        md_dict = {}
        md_dict["name"] = self.name
        md_dict["description"] = self.description
        md_dict["tags"] = self.tags
        md_dict["id"] = self.id
        md_dict["filename"] = self.filename
        md_dict["version"] = self.version

        return json.dumps(md_dict, indent=4)


default_module = Module("file", "<Unknown>", "<No description>", [], "<Unknown>", None)

# unpack function for list[Module] -> good data for new_table() 
# returns [[ids], [name], [descriptions], [tags as a string]]
def get_module_data(modules: list[Module]):
    ids = []
    names = []
    descriptions = []
    tags = []
    versions = []
    for m in modules:  # i do not need to document this shit you can tell what it does just read the code
        ids.append(str(m.id))
        names.append(m.name)
        descriptions.append(m.description)
        tags.append(", ".join(m.tags))
        versions.append(str(m.version))
    return [ids, names, descriptions, tags, versions]

# intialize rich console and module table arrays
console = console.Console()
modules = []

# ansi colours
reset = "\x1b[0m"
italic = "\x1b[3m"
bold = "\x1b[1m"
cyan = "\x1b[38;5;6m"
green = "\x1b[38;5;2m"
yellow = "\x1b[38;5;3m"
red = "\x1b[38;5;9m"
grey = "\x1b[38;5;8m"

# bone-chillingly beautiful formatting
tutorial_str = f"""  
Welcome to the module system tutorial!
To select an action, type its {yellow}name{reset} or its corresponding {green}ID{reset}.
If you want to go back to the action selection, type {cyan}back{reset}.
If you can't see any modules, cehck your tags in the settings.

List of current settings:
{green}filter_tags{reset} (list): {yellow} A list of tags that modules are filtered by. Modules without these tags will not show up in the module selection. {reset}
{green}module_server{reset} (IPv4 Address): {yellow} The server that stores modules. By default, it is XXX.XXX.XXX.XXX{reset}
{green}confirm_delete{reset} (True / False): {yellow} Confirms with user before deleting a module. True by default {reset}
{green}ignore_str{reset} (string): {yellow} A string that modules are filtered by. 
Modules with this string in their code will not show up in the module selection. {reset}
{green}ignore_filter{reset} (True / False): {yellow} Toggles the previous setting. True by default. {reset} 


If you want to create your own module, follow the instructions below:
1. Create a new python file (.py)
2. put these comments in the file (comments begin with "{bold}# {reset}") that say:
 - the name of the module in this format: {bold}# name: [Name] {reset}
 - a description of the module in this format: {bold}# description: some module {reset}
 - tags for the module in this format: {bold}# tags: tag1, tag2, tag3 {reset}
    * these tags must be separated by a comma and a space: ", "
 - optionally a version
3. put it in the /modules folder or import it through the program 

{reset}{italic}{grey}Made by </> (arrow) on 2025/03/19, last updated on v0.2.1 at 2025/03/26{reset}
"""  # add stuff later when added

# name, desc, tags, version, 
boilerplate = """# name: <NAME>
# description: <DESC>
# tags: <TAGS>
# version: 1
# made by <USER> on <DATE>
import utils

def solver():
    pass
"""

# module table
titles = {  # constant
    "ID": {"style": "cyan", "justify": "right"},
    "Module Name": {"style": "green", "justify": "right"},
    "Module Description": {"style": "yellow", "justify": "left"},
    "Tags": {"style": "red", "justify": "left"},
    "Version": {"style": "purple", "justify": "right"}
}

# settings
settings = {}
setting_data = {}

def update_settings():
    global settings, setting_data
    raw_settings = json.load(open("settings.json", "r"))
    settings = {k: v[1] for k, v in raw_settings.items()}
    setting_data = {k: v[0] for k, v in raw_settings.items()}


# parse num util function
# maybe put the inside of a utils.py?
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
def new_table(name: str, titles: dict, rows: list[list]):
    module_table = table.Table(title=name)
    for title, formatting in titles.items():
        module_table.add_column(title, justify=formatting["justify"], style=formatting["style"])
    for vals in zip(*rows):
        module_table.add_row(*vals)
    return module_table


def get_valid_input(input_message: str, valid_inputs: list[str], indices: bool=False, back_enabled : bool=True, err_word: str="input"):
    valid_inputs.extend([str(i) for i in range(len(valid_inputs))] if indices else [])
    choice = ""
    while True:
        inp = input(input_message).rstrip()
        if inp == "back" and back_enabled:
            choice = "\0"
            break
        
        if inp not in valid_inputs:
            print(f"{inp} is not a valid {err_word}, please try again.")
            continue

        if indices and type(parse_num(inp)) == int:
            choice = valid_inputs[int(inp)]
            break
        else:
            choice = inp
            break

    return choice


def get_metadata(file: str):
    current_module = copy.deepcopy(default_module)
    ignore = False
    with open(file, "r") as f:
        lines = f.read().split("\n")
        for line in lines:
            if "# name: " in line:
                current_module.name = line.split("# name: ")[1]
            if "# description: " in line:
                current_module.description = line.split("# description: ")[1]
            if "# tags: " in line:  
                current_module.tags = line.split("# tags: ")[1].split(", ")
            if "# version: " in line:
                current_module.version = int(line.split("# version: ")[1])
            if settings["ignore_str"] in line.lower():
                ignore = True
    return current_module if not ignore else "IGNORE"


def refresh_modules():
    global modules
    # TODO: update old modules (version number) when downloading
    module_files = [m for m in os.listdir("modules") if m.endswith(".py") and os.path.isfile(f"modules/{m}")]

    modules = []
    # populate arrays from /modules
    for m in range(len(module_files)):
        # get metadata from within file
        current_module = copy.deepcopy(default_module)

        try:
            meta = get_metadata(f"modules/{module_files[m]}")
            if meta == "IGNORE":
                continue
            current_module = meta
        except FileNotFoundError:
            print(f"Could not access {module_files[m]}: Not found in /modules (how did you move this shit out of modules/ already??)")
        except PermissionError:
            print(f"Could not access {module_files[m]}: Permission denied")
        except Exception as e:
            print(f"couldnt read {module_files[m]} cuz {e}")

        # get the rest of metadata
        current_module.filename = module_files[m]
        current_module.id = m
       
        modules.append(current_module)
    
    print(f"Loaded {len(modules)} modules successfully")


def update_module_table():
    global titles, modules, module_table, module_table_data
    refresh_modules()
    module_table_data = get_module_data(modules)
    module_table = new_table("Installed Modules", titles, module_table_data)


# returns module filename
def module_select():
   
    # update table at execution time to account for imported modules
    update_module_table()
    console.print(module_table)

    module_names = [m.name for m in modules]
    
    choice = get_valid_input(f"> Select a module by {cyan}ID{reset} or {green}name{reset}: ", module_names, True, "module")
    if choice == "\0":  
        return
    # map choice index to module
    choice_index = module_names.index(choice)
    return modules[choice_index]


""" do we use a @server decorator for auth and session handling?
All actions:
- Select a module [DONE]
- List all modules [DONE]
- Update a module [SERVER]
- Update all modules [SERVER]
- Create a new module [DONE]
- Remove a module [DONE] 
- Import module from file [DONE]
- Import module from server [SERVER]
- Export module to server [SERVER]
- print all available modules on server [SERVER]
- Change settings [DONE]
- Print user guide [DONE]
- Exit [DONE]
"""

def action_select():
    actions = ['Select a module', 'List all modules', 'Update a module', 'Update all modules', 'Create a new module', 'Remove a module', 'Import module from file', 'Import module from server', 'Export module to server', 'Print all modules on server', 'Change settings', 'Print user guide', 'Exit']

    ids = [str(i) for i in range(len(actions))]
    titles = {
        "ID": {"style": "green", "justify": "right"},
        "Action": {"style": "yellow", "justify": "left"}
    }
    action_table_data = [ids, actions]
    action_table = new_table("Actions", titles, action_table_data)
    console.print(action_table)
    choice = get_valid_input(f"> Select an action by its {green}ID{reset} or {yellow}name{reset}: ", actions, True, False)
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
    if module_obj:
        try:
            module_obj.solver()
        except Exception as e:
            print(f"{red}{module.name} crashed :({reset}")
    else:
        print(f"{module.name} does not have a solver() function. Unable to run module.")


# todo: whole lotta settings (for a whole loota things)
def change_settings():
    settings_table = table.Table(title="Settings")
    settings_table.add_column("ID", justify="right", style="cyan")
    settings_table.add_column("Setting", justify="left", style="green")
    settings_table.add_column("Value", justify="left", style="yellow")
    settings_table.add_column("Data Type", justify="left", style="red")
    
    for i in range(len(settings)):
        setting = list(settings.keys())[i]
        value = str(settings[setting])
        data_type = str(setting_data[setting])
        settings_table.add_row(str(i), setting, value, data_type)

    console.print(settings_table)
    choice = get_valid_input(f"> Select the setting you want to change by its {cyan}ID{reset} or {green}name{reset}: ", list(settings.keys()), True, err_word="setting")
    if choice == "\0":
        return
    settings[choice] = input(f"Enter the new value for {choice}: ")
    json.dump(settings, open("settings.json", "w"))


def server_module_select():
    pass


def local_file_select():
    # get file
    try:
        selected_file = easygui.fileopenbox()
        filename = selected_file.split("/")[-1]
    except Exception as e:
        print("Unable to open file dialog")
    
    # filter out bad input
    if ~filename.endswith(".py"):
        print("Invalid input file. Please select a .py file.")
        return
    
    # check if it is already in the modules directory
    if filename in os.listdir("modules"):
        choice = prompt.Prompt.ask(f"{filename} is already in the modules directory. Do you want to replace it? [yes/no]: ")
        if choice.lower() == "no" or not choice:
            return
    
    # check for solver function
    if ~check_module(filename):
        print(f"{selected_file} does not have a solver() function. It cannot be ran as a module and will not be imported.")
    
    try:  # copy file to modules/ directory
        shutil.copy(selected_file, "modules")
        print(f"Loaded {filename} successfully")
    except Exception as e:
        print(f"Could not read {selected_file} because {e}")


def delete_module():
    module = module_select()
    if settings["confirm_delete"]:
        if not prompt.Prompt.ask(f"Are you sure you want to delete {module.name} ({module.filename})?"):
            return
    os.remove(f"modules/{module.filename}")


def create_module():
    filename = input("> Enter the filename of the new module: ")
    if filename.endswith(".py"):
        filename = filename[:-3]  # remove .py
    content = copy.copy(boilerplate)

    name = input("> Enter the name of the module: ")
    description = input("> Enter the description for this module: ")
    tags = ", ".join(sorted(list(set([t.rstrip().lstrip() for t in input("> Enter tags separated by commas: ").split(",") if t]))))
    user = input("> Enter your username: ")
    date = time.strftime("%Y/%m/%d", time.localtime())

    # put all the data into the boilerplate
    content = content.replace("<USER>", user)
    content = content.replace("<NAME>", name)
    content = content.replace("<DESC>", description)
    content = content.replace("<TAGS>", tags)
    content = content.replace("<DATE>", date)

    with open(f"modules/{filename}.py", "w") as f:
        f.write(content)

    print(f"successfully created {filename}.py")


## SERVER STUFF ##
session = None
online = False
last_ping = 0



headers = {
    "Content-Type": "application/json"
}

# payloads:
# "ping": {} -> pong
# "session": {"pwd": password} -> session
# "gitfetch": {"session": session} -> ?
# "version": {"mod": [module names], "session": session} -> version number(s)
# "install": {"mod": [module names], "session": session} -> module file(s)
# "list": {include_ignores: bool, "session": session} -> list of all modules on server

payloads = {
    "ping": [],
    "pong": [],  
    "session": ["pwd"],
    "gitfetch": ["session"],
    "version": ["mod", "session"],
    "metadata": ["mod", "session"],
    "install": ["mod", "session"],
    "upload": ["mod", "session"],
    "list": ["include_ignores", "session"]
}


def get_bool(msg):
    return input(msg).lower()[0] == "y"


def get_server_pw():
    pw = settings["server_pw"]
    if len(pw) <= 0: 
        pw = input("Enter password for server: ")
    return pw

def format_payload(payload: str):
    global session
    if payload not in payloads:
        return
    
    ready_payload = {
        "action": payload
    }

    match payload:
        case "session":
            ready_payload["pwd"] = get_server_pw()
        case "list":
            ready_payload["session"] = session
        case "install":
            ready_payload["session"] = session
            ready_payload["mod"] = [m.rstrip().lstrip() for m in input("> Enter the module to install (or multiple separated by commas)").split(",")] 
        case "gitfetch":
            ready_payload["session"] = session
        case "version":
            ready_payload["session"] = session
            ready_payload["mod"] = [m.rstrip().lstrip() for m in input("> Enter the module to install (or multiple separated by commas)").split(",")] 
        case "metadata":
            ready_payload["session"] = session
            ready_payload["mod"] = [m.rstrip().lstrip() for m in input("> Enter the module to install (or multiple separated by commas)").split(",")] 
        case "upload":
            ready_payload["session"] = session
            ready_payload["overrideVersion"] = get_bool("> Override the existing module's version number? [y/n]: ")
            ready_payload["overrideMod"] = get_bool("> Override the module if it exists on the server? [y/n]: ")
            selected_module = module_select().filename 
            with open(f"modules/{selected_module}", "r") as f:
                ready_payload["data"] = f.read()
            ready_payload["filename"] = selected_module
        case _:
            pass

    print("sending payload:", ready_payload)
    return ready_payload

# returns true if server is online
def test_ping():
    global last_ping
    req = requests.post(f"https://{settings['module_server']}", json=format_payload("ping"), headers=headers)
    last_ping = time.time()

    # display appropriate message according ot stateus code
    match req.status_code:
        case 200:
            print(f"Server {settings['module_server']} is online ({req.status_code})")
            return True
        case 523:
            print(f"Server {settings['module_server']} is offline / unreachable")
            return False
        case 400:
            print(f"Bad requests: {req.status_code}") 
        case _:
            print(f"Unknown error: {req.status_code} (server told you to kys)")

def get_session():
    payload = format_payload("session")
    req = requests.post(f"https://{settings['module_server']}",json=payload, headers=headers)

    # parse response
    success = json.loads(req.text)["success"]

    if success == 0:
        print("Invalid password; unable to generate session")
        return
    session = json.loads(req.text)["data"]

    return session



def reconnect():
    if last_ping + 60 < time.time():
        print("Server is offline. Unable to perform action.")
    else:
        print("Server is offline. Attempting to reconnect...")
        online = test_ping()
        if online:
            return "yes"
    return "no"


def server_required(func):
    def wrapper(*args, **kwargs):
        global session
        # check if server is online
        if not online:
            if reconnect() == "no":
                return

        # assumes server is online
        if not session:
            session = get_session()
        func(*args, **kwargs)
    return wrapper


@server_required
def list_modules():
    # send payload
    payload = format_payload("list")
    req = requests.post(f"https://{settings['module_server']}/", json=payload, headers=headers)

    response = json.loads(req.text)
    print("list_modules response:", response)
    if response["success"] == 0:
        print(f"Could not list modules.")
    else:
        print(f"{response['data']}")  # todo: format modulse into table


def action_controller(action: str):
    match action:
        case "Select a module":
            module = module_select()
            print(f"\n-----------[ {green}Start of {module.name} {reset}]-----------")
            load_module(module)
            print(f"------------[ {red}End of {module.name} {reset}]------------\n")
        case "List all modules":
            update_module_table()
            console.print(module_table)
        case "Import module from file":
            local_file_select()
        case "Import module from server":
            server_module_select()
            print("not implemented yet")  # todo: prompt user with input dialog: get valid input (valid_inputs = modules.txt on server) -> download module from server -> add to /modules
        case "Export a module to server":
            print("not implemented yet")
        case "Update a module":
            print("not implemented yet")
        case "Update all modules":
            print("not implemented yet")
        case "Create a new module":
            create_module()
        case "Remove a module":
            delete_module()
        case "Print all modules on server":
            list_modules()
        case "Change settings":  # TODO: implement filtering by tags
            change_settings()
        case "Print user guide":
            print(tutorial_str)
        case "Exit":
            print("Exiting...")
            exit(0)


def main():
    global online
    os.system("cls" if os.name == "nt" else "clear") 
    update_settings()
    online = test_ping()

    while True:
        action_controller(action_select())
        update_settings()

if __name__ == "__main__":
    main()
