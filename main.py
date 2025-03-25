import os, importlib.util, json, easygui, shutil, copy
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
module_name = []

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

If you want to create your own module, follow the instructions below:
1. Create a new python file (.py)
2. put these comments in the file (comments begin with "{bold}# {reset}") that say:
 - the name of the module in this format: {bold}# name: [Name] {reset}
 - a description of the module in this format: {bold}# description: some module {reset}
 - tags for the module in this format: {bold}# tags: tag1, tag2, tag3 {reset}
    - these tags must be separated by a comma and a space: ", "
3. put it in the /modules folder or import it through the program 

{reset}{italic}{grey}Made by </> (arrow) on 2025/03/19, last updated v0.1.1{reset}
"""  # add stuff later when added

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

def update_settings():
    global settings
    settings = json.load(open("settings.json", "r"))


def display_settings():
    settings_table = table.Table(title="Settings")
    settings_table.add_column("Setting", justify="right", style="green")
    settings_table.add_column("Value", justify="left", style="yellow")
    for setting, value in settings.items():
        settings_table.add_row(setting, value)

    console.print(settings_table)


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
            if "# ignore" in line.lower():
                ignore = True
    return current_module if not ignore else "IGNORE"


def refresh_modules():
    global modules, module_names
    # TODO: update old modules (version number)
    # TODO: ingore modules if there is # IGNORE in metadata
    # TODO: include a utils.py file in modules/ that has common functions
    module_files = [m for m in os.listdir("modules") if m.endswith(".py") and os.path.isfile(f"modules/{m}")]

    modules = []
    module_names = []
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
        module_names.append(current_module.name)
    
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
    
    choice = get_valid_input(f"> Select a module by {cyan}ID{reset} or {green}name{reset}: ", module_names, True, "module")
    if choice == "\0":
        return
    # map choice index to module
    choice_index = module_names.index(choice)
    return modules[choice_index].filename


"""
All actions:
- Select a module [DONE]
- Import module from file
- Import module from server [SERVER]
- Export module to server [SERVER]
- update a module [SERVER]
- update all modules [SERVER]
- remove a module 
- print all available modules on server [SERVER]
- Change settings [DONE]
- Print user guide [DONE]
- Exit [DONE]
"""

def action_select():
    actions = ["Select a module", "Import module from file", "Import module from server", "Export a module to server", "Update a module", "Update all modules", "Remove a module", "Print all importable modules", "Change settings", "Print user guide", "Exit"]
    lower_actions = [a.lower() for a in actions]
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


def load_module(module: str):
    module = check_module(f"modules/{module}")
    if module:
        module.solver()
    else:
        print(f"{module} does not have a solver() function. unable to run module.")


def change_settings():
    settings_table = table.Table(title="Settings")
    settings_table.add_column("ID", justify="right", style="cyan")
    settings_table.add_column("Setting", justify="left", style="green")
    settings_table.add_column("Value", justify="left", style="yellow")
    id = 0
    for setting, value in settings.items():
        settings_table.add_row(str(id), setting, f"{value}")
        id += 1

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
    selected_file = easygui.fileopenbox()
    filename = selected_file.split("/")[-1]

    # filter out bad input
    if ~filename.endswith(".py"):
        print("Invalid input file. Please select a .py file.")
        return
    
    # check if it is already in the modules directory
    if filename in os.listdir("modules"):
        choice = prompt.Prompt.ask(f"{filename} is already in the modules directory. Do you want to replace it? [yes/no]: ")
        if choice == "no" or not choice:
            return
    
    # check for solver function
    if ~check_module(filename):
        print(f"{selected_file} does not have a solver() function. It cannot be ran as a module and will not be imported.")
    
    try:  # copy file to modules/ directory
        shutil.copy(selected_file, "modules")
        print(f"Loaded {filename} successfully")
    except Exception as e:
        print(f"Could not read {selected_file} because {e}")


def action_controller(action: str):
    match action:
        case "Select a module":
            module = module_select()
            print(f"\n-----------[ {green}Start of {module} {reset}]-----------")
            load_module(f"{module}")
            print(f"------------[ {red}End of {module} {reset}]------------\n")
        case "Import module from file":
            local_file_select()
        case "Import module from server":
            print("not implemented yet")  # todo: prompt user with input dialog: get valid input (valid_inputs = modules.txt on server) -> download module from server -> add to /modules
        case "Export a module to server":
            print("not implemented yet")
        case "Update a module":
            print("not implemented yet")
        case "Update all modules":
            print("not implemented yet")
        case "Remove a module":
            print("not implemented yet")
        case "Print all importable modules":
            print("not implemented yet")
        case "Change settings":  # TODO: implement filtering by tags
            change_settings()
        case "Print user guide":
            print(tutorial_str)
        case "Exit":
            print("Exiting...")
            exit(0)


def main():
    os.system("cls" if os.name == "nt" else "clear") 

    while True:
        update_settings()
        action_controller(action_select())
        

if __name__ == "__main__":
    main()
