try:
    import os, importlib.util, json, easygui, shutil, copy, time, requests, ping3
    from rich import console, table
except ModuleNotFoundError:
    print("[\x1b[38;5;9mFATAL\x1b[0m] \x1b[38;5;9mThe requied modules are not installed. Please install them by running the command 'pip install -r requirements.txt'\x1b[0m")
    quit()

# ansi colours
reset = "\x1b[0m"
italic = "\x1b[3m"
bold = "\x1b[1m"
cyan = "\x1b[38;5;6m"
green = "\x1b[38;5;2m"
yellow = "\x1b[38;5;3m"
red = "\x1b[38;5;9m"
saturated_red = "\x1b[38;5;196m"
grey = "\x1b[38;5;8m"


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

    # pretty-print metadata dict
    def __str__(self):
        md_dict = {}
        md_dict["name"] = self.name
        md_dict["description"] = self.description
        md_dict["tags"] = self.tags
        md_dict["id"] = self.id
        md_dict["filename"] = self.filename
        md_dict["version"] = self.version

        return json.dumps(md_dict, indent=4)
    
    # nicely-formatted string
    def get_str(self):
        return f"{green}{self.name}{reset} ({yellow}{self.filename}{reset})"
    
# settings struct for convenience
class Setting:
    def __init__(self, name, type, value, description):
        self.type = type
        self.value = value
        self.name = name
        self.description = description


default_module = Module("file", "<Unknown>", "<No description>", [], "<Unknown>", None)

# unpack function for list[Module] -> good data for new_table() 
# returns [[ids], [name], [descriptions], [tags as a string]]
def get_module_data(modules: list[Module]):
    ids = []
    names = []
    descriptions = []
    tags = [] 
    versions = []
    for m in modules:  # formats everything properly so rich can display it
        ids.append(str(m.id))
        names.append(m.name)
        descriptions.append(m.description)
        tags.append(", ".join(m.tags))
        versions.append(str(m.version))
    return [ids, names, descriptions, tags, versions]

# intialize rich console and module table arrays
console = console.Console()
modules = []

# user guide
tutorial_str = f"""\n----------------------------------------------------------------------- 
Welcome to the problem set solver tutorial!

{bold}## USAGE{reset}
To select an action, type its {yellow}name{reset} or its corresponding {green}ID{reset}.

To get started, download a module from the server by typing 7.
Once at the module selection screen, you can select modules by name or number. To install mutiple modules, type their corresponding numbers or names separated by spaces (e.g. 1, 2, 3)
You can now run these modules by typing 0 at the action selection, and selecting the module you want to run. You can only select one module to run at a time.
If a module crashes, an error will appear displaying the crash message.

If you want to delete all modules, type 'all' or 'everything' at the module delte prompt.
Similarly, if you want to download all modules on the server, type 'all' or 'everything' at its respective prompt.

If you want to go back to the action selection from any prompt, type {cyan}back{reset}.
If you want to send feedback or suggest a feature, select action 12 and enter the feedback.

{bold}## COMMON PROBLEMS{reset}
If you can't see any modules, they might still be downloading from the server, or your tag search is filtering them out.
To change the tag search, go to the settings changer by typing 10 and follow the instructions.

{bold}## MODULES{reset}
To create a module, you must know how to write basic code in python, and if you want to work with complex equations, learn how to use SymPy.
Your modules should not contain any dependencies or import other than utils.
If you don't know how to write code, you can contact me to make it at @arrowslasharrow on Discord.

{reset}{italic}{grey}Made by </> (arrow) and bitfeller on 2025/03/19, last updated on v1.0.1 at 2025/03/31{reset}
-----------------------------------------------------------------------
"""  

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
    "Change settings": "set",
    "Print user guide": "guide",
    "Send feedback": "sfb",
    "Exit": "x"
}

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


# update the various settings arrays
def update_settings():
    global settings, setting_data
    raw_settings = json.load(open("settings.json", "r"))
    for key in list(raw_settings.keys()):
        settings[key] = (Setting(key, *raw_settings[key][0:3]))


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


def get_valid_input(input_message: str, valid_inputs: list[str], indices: bool=False, back_enabled : bool=True, err_word: str="input", many=False, everything=False):
    original_inputs = copy.deepcopy(valid_inputs)
    valid_inputs.extend([str(i) for i in range(len(valid_inputs))] if indices else [])    
    if not many:
        choice = ""
        while True:
            inp = input(input_message).lower().rstrip().lstrip()
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
    else:
        choices = []
        inp = [i.lstrip().rstrip() for i in input(input_message).split(",")]
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


def get_metadata(file: str):
    current_module = copy.deepcopy(default_module)
    ignore = False
    raw_data = open(file, "r").read()

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


def refresh_modules():
    global modules
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
    
    if len(modules) > 0:
        print(f"Loaded {len(modules)} modules successfully")


def update_module_table():
    global module_table, module_table_data
    refresh_modules()
    if len(modules) == 0:
        print("No modules found in modules/")

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
    module_table = new_table("Installed Modules", titles, module_table_data)


# returns module filename
def module_select(other_valid_inputs=[]):
   
    # update table at execution time to account for imported modules
    update_module_table()
    # info messages
    if len(settings['filter_tags'].value) > 0:
        print(f"Searching by these tags: {', '.join(settings['filter_tags'].value)}")
    print("If no modules show up, type 'back' and try again in a few seconds,. or check your tags setting.")
    console.print(module_table)

    # get module
    module_names = [m.name for m in modules]
    module_names.extend(other_valid_inputs)
    choice = get_valid_input(f"> Select a module by {cyan}ID{reset} or {green}name{reset}: ", module_names, True, "module")
    if choice == "\0":  
        return
    if choice in other_valid_inputs:
        return choice
    # map choice index to module
    choice_index = module_names.index(choice)
    return modules[choice_index]


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
    available_actions = copy.copy(lower_actions)
    available_actions.extend(shorthand)
    choice = get_valid_input(f"> Select an action by its {green}ID{reset} or {yellow}name{reset}{f' or {red}shorthand{reset}' if settings['shorthand_actions'].value else ''}: ", available_actions, indices=True, err_word="action")
    
    if choice in shorthand:
        choice = full_actions[shorthand.index(choice)]
    elif choice in lower_actions:
        choice = full_actions[lower_actions.index(choice)]
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
        print(f"\n{module.name} does not have a solver() function. Unable to run module.\n")


def boolstr(s: str):
    return s.lower() in ("true", "yes", "ye", "1", "yep", "yea", "yeah")


def format_settings(settings: list[Setting]):
    raw_settings = {}
    for setting in list(settings.values()):
        raw_settings[setting.name] = [setting.type, setting.value, setting.description]
    return raw_settings


def change_settings():
    # initialize table and columns
    settings_table = table.Table(title="Settings")
    settings_table.add_column("ID", justify="right", style="cyan")
    settings_table.add_column("Setting", justify="left", style="green")
    settings_table.add_column("Value", justify="left", style="yellow")
    settings_table.add_column("Description", justify="left", style="red")
    settings_table.add_column("Data Type", justify="left", style="purple")
    
    # populate settings table
    index = 0
    for setting in list(settings.values()):
        name = setting.name
        value = str(setting.value)
        data_type = setting.type
        description = setting.description
        settings_table.add_row(str(index), name, value, description, data_type)
        index += 1

    console.print(settings_table)
    choice = get_valid_input(f"> Select the setting you want to change by its {cyan}ID{reset} or {green}name{reset}: ", list(settings.keys()), True, err_word="setting")
    if choice == "\0":
        return
    
    inp = input(f"Enter the new value for {choice}: ")
    
    # format input according to data type
    match settings[choice].type:
        case "boolean":
            inp = boolstr(inp)

    # change and save setting
    settings[choice].value = inp
    json.dump(format_settings(settings), open("settings.json", "w"), indent=4)


def local_file_select():
    # get file
    try:
        selected_file = easygui.fileopenbox()
        if not selected_file:
            return
        filename = selected_file.split("/")[-1]
    except Exception as e:
        print("Unable to open file dialog")
        return  # todo: file select through path
    
    # filter out bad input
    if not filename.endswith(".py"):
        print("Invalid input file. Please select a .py file.")
        return
    
    # check if it is already in the modules directory
    if filename in os.listdir("modules"):
        choice = get_bool(f"{filename} is already in the modules directory. Do you want to replace it? [yes/no]: ")
        if not choice:
            return
    
    # check for solver function
    if not check_module(filename):
        print(f"{selected_file} does not have a solver() function. It cannot be ran as a module and will not be imported.")
    
    try:  # copy file to modules/ directory
        shutil.copy(selected_file, "modules")
        print(f"Loaded {filename} successfully")
    except Exception as e:
        print(f"Could not read {selected_file} because {e}")


def delete_module():
    all = ["all", "everything"]
    module = module_select(other_valid_inputs=all)
    if not module:
        return
    
    if module in all:
        if not get_bool(f"[{saturated_red}WARNING{reset}] {red}This action is irreversible. Are you absolutely sure you want to delete every single module you have installed?{reset} [yes/no]: "):
            return
        
        try:
            for file in [f for f in os.listdir("modules") if f != "utils.py"]:
                os.remove(f"modules/{file}")
        except Exception as e:
            pass
    else:
        if settings["confirm_delete"].value:
            if not get_bool(f"Are you sure you want to delete {module.name} ({module.filename})? [yes/no] "):
                return
        os.remove(f"modules/{module.filename}")


def create_module():
    filename = input("> Enter the filename of the new module: ")
    if filename == "back":
        return
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
server = ""

headers = {
    "Content-Type": "application/json"
}

def get_bool(msg):
    return input(msg).lower()[0] == "y"


def get_server_pw():
    pw = settings["server_pw"].value
    if len(pw) <= 0: 
        pw = input("Enter password for server: ")
    return pw


def format_payload(payload: str, modules=[], feedback=""):
    global session
    
    ready_payload = {
        "action": payload
    }

    match payload:
        case "session":
            ready_payload["pwd"] = get_server_pw()
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
            ready_payload["overrideVersion"] = get_bool("> Override the server module's version number? [yes/no]: ")
            ready_payload["overrideMod"] = get_bool("> Override the module if it exists on the server? [yes/no]: ")
        case "feedback":
            ready_payload["session"] = session
            ready_payload["feedback"] = feedback
        case _:
            pass

    if settings["show_requests"].value:
        print(f"[{yellow}PAYLOAD{reset}] {ready_payload}")

    return ready_payload


def show_response(req):
    if settings["show_requests"].value:
        colour = red if json.loads(req.text)["success"] == 0 else green
        print(f"[{colour}RESPONSE{reset}] {req.text}")


def send_request(payload):
    req = requests.post(server, json=payload, headers=headers)
    show_response(req)
    if json.loads(req.text)["data"] == "easter egg":
        print(r"easter egg triggered lmao goodbye (this is a 0.1% chance)")
        quit()
    return req


# returns true if server is online
def test_ping(mode="ready"):
    global last_ping
    try:
        if mode == "exists":
            ping = ping3.ping(settings["module_server"].value)
            match ping:
                case False:
                    print("Server does not exist. Unable to connect")
                case None:
                    print("server did not respond to ping. Unable to connect")
                case _:
                    print(f"Server exists")
        else:
            req = send_request(format_payload("ping"))
            last_ping = time.time()
            # display appropriate message according ot stateus code
            match req.status_code:
                case 200:
                    print(f"Server {settings['module_server'].value} is online (latency: {req.elapsed.seconds * 500 + req.elapsed.microseconds / 2000 :.2f}ms)")
                    print(f"Message from server: {json.loads(req.text)['data']}")
                    return True
                case 523:
                    print(f"Server {settings['module_server'].value} is offline")
                case 504:
                    print("Gateway Timeout (504). Server is offline") 
                case 500:
                    print("Server is updating (500). Server is offline")
                case _:
                    print(f"Unknown error: {req.status_code} (server told you to kys)")
    except json.decoder.JSONDecodeError:
        print("Server responded with bad JSON, and is likely down.")
    except Exception as e:
        print("Could not connect to the server for this reason:", e)    
    return False


def get_session():
    payload = format_payload("session")
    req = send_request(payload)

    # parse response
    success = json.loads(req.text)["success"]
    data = json.loads(req.text)["data"]

    if success == 0:
        if data == "bad pwd":
            print(f"Invalid password; unable to generate session. If the {yellow}server_pw{reset} value is set, it might be set to the wrong password. ")
        return
    session = data

    return session


def reconnect():
    if last_ping + 60 < time.time():
        print("Server is offline. Unable to perform action.")
    else:
        print("Server is offline. Attempting to reconnect...")
        online = test_ping()
        if online:
            return True
    return False


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
def list_server_modules():
    global session
    # send payload
    payload = format_payload("list")
    req = send_request(payload)

    response = json.loads(req.text)
    if response["success"] == 0:
        if response['data'] == 'bad session':
            session = get_session()
        print(f"Could not list modules.")
        return

    if len(response['data']) == 0:
        print("No modules in here")
        return
    
    modules = []
    for name, meta in response["data"].items():
        new_mod = copy.deepcopy(default_module)
        new_mod.name = name
        new_mod.description = meta["desc"]
        new_mod.version = meta["version"]
        new_mod.filename = meta["filename"]
        new_mod.tags = meta["tags"]
        new_mod.id = str(len(modules))
        modules.append(new_mod)

    server_module_table = new_table(f"Modules on {settings['module_server'].value}", titles=titles, rows=get_module_data(copy.deepcopy(modules)))
    console.print(server_module_table)

    return modules


@server_required
def server_module_select():
    available_modules = list_server_modules()
    selected_modules = get_valid_input(f"> Select module(s) by {cyan}ID{reset} or {green}name{reset} (separated by commas if there are multiple): ", available_modules, True, "module", many=True, everything=True)
    if selected_modules == "\0":
        return

    print(selected_modules)
    payload = format_payload("install", modules=selected_modules)
    req = send_request(payload)
    resp = json.loads(req.text)["data"]
    for mod in resp:  # mod: [metadata dict, contents]
        filename = ""
        name = ""
        try:
            filename = mod[0]["filename"]
            name = mod[0]["name"]
        except Exception as e:
            pass

        if filename in os.listdir("modules"):
            choice = get_bool(f"{green}{name}{reset} ({yellow}{filename}{reset}) is already in the modules directory. Do you want to replace it? [yes/no]: ")
            if not choice:
                continue
    
        with open(f"modules/{filename}", "w") as m:
            m.write(mod[1])


@server_required
def upload_module():
    payload = format_payload("upload")
    if payload == "\0":
        return
    req = send_request(payload)
    if json.loads(req.text)["success"]:
        print("Module uploaded successfully.")
    else:
        print("Module upload failed")

@server_required
def update_module(module=""):
    if module == "":
        module = module_select()
        if not module: 
            return
        
    req = send_request(format_payload("version", [module]))
    if json.loads(req.text)["success"] == 1:
        version = int(json.loads(req.text)["data"][0])
        module_version = int(module.version) if type(parse_num(module.version)) == int else -1

        if module_version < version:
            payload = format_payload("install", modules=[module])
            req = send_request(payload)
            mod = json.loads(req.text)["data"][0]
            
            with open(f"modules/{module.filename}", "w") as m:
                m.write(mod[1])    
            print(f"Updated {module.get_str()}")
        else:
            print(f"{module.get_str()} is already up to date.")
    else:
        match json.loads(req.text)["data"]:
            case "no mod":
                print(f"Unable to update {module.get_str()} because it is not on the server.")
            case _:
                print(f"Unable to update {module.get_str()}")


def update_all():
    refresh_modules()
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
            print("Thanks for your feedback :)")
            return
    except Exception as e:
        print(f"{red}error: {e}{reset}")
    # print this if bad params or crash 
    print("Unable to send feedback :(")



def action_controller(action: str):
    match action:
        case "Select a module":
            module = module_select()
            if not module:
                return
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
        case "Print user guide":
            print(tutorial_str)
        case "Send feedback":
            send_feedback()
        case "Exit":
            print("Exiting...")
            send_request(format_payload("exit")) if session else 0
            exit(0)


def preload():
    global online, server
    os.system("cls" if os.name == "nt" else "clear")

    # create /modules if it does not exist
    if not os.path.exists("modules"):
        os.mkdir("modules")
        print(f"{red}The modules/ directory was not found and was replaced. The utils.py is now lost from it, please redownload it from the GitHub repository (ArrowSlashArrow/problem-set-solver-v2). {reset}")
    
    # load settings
    update_settings()
    
    # ping server and check connection
    server = f"https://{settings['module_server'].value}/"
    print('Testing server connectivity... ') 
    test_ping(mode="exists")
    online = test_ping()

    # autoupdate
    if settings["autoupdate_modules"].value:
        try:
            updating = len([f for f in os.listdir("modules") if f != "utils.py" and f.endswith(".py")])
            print(f"\nUpdating {updating} module{'s' if updating != 1 else ''}...")
            update_all()
        except Exception as e:
            print(f"{red}Could not autoupdate modules.{reset}")
    print(tutorial_str)


def main():
    preload()

    while True:
        action_controller(action_select())
        update_settings()

if __name__ == "__main__":
    main()
