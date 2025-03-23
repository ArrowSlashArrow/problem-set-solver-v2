import os, importlib.util, json
from rich import console, table

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

# bone-chillingly beautiful ascii art
tutorial_str = f"""  
Welcome to the module system tutorial!
To select an action, type its {yellow}name{reset} or its corresponding {green}ID{reset}.
If you want to create your own module, follow the instructions below:
1. Create a new python file (.py)
2. put three comments in the file (comments begin with #) that say:
 - the name of the module (e.g. # name: Module)
 - a description of the module (e.g. # description: some module)
3. put it in the /modules folder or import it through the program 

{reset}{italic}{grey}Made by </> (arrow) on 2025/03/19, last updated v0.1.0{reset}
"""  # add stuff later when added

# module table
titles = {  # constant
    "ID": {"style": "cyan", "justify": "right"},
    "Module Name": {"style": "green", "justify": "right"},
    "Module Description": {"style": "yellow", "justify": "left"}
}

descriptions = []
module_names = []
ids = [str(i) for i in range(len(modules))]
module_table_data = [ids, module_names, descriptions]
module_table = table.Table(title="Installed Modules")

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


def get_valid_input(input_message: str, valid_inputs: list[str], indices: bool=False, back_enabled :bool=True, err_word: str="input"):
    valid_inputs.extend([str(i) for i in range(len(valid_inputs))] if indices else [])
    while True:
        inp = input(input_message).rstrip()
        if inp == "back" and back_enabled:
            return "\0"
        if inp not in valid_inputs:
            print(f"{inp} is not a valid {err_word}, please try again.")
            continue
        else:
            if indices and type(parse_num(inp)) == int:
                return valid_inputs[int(inp)]
            else:
                return inp


def refresh_modules():
    global modules
    modules = [m for m in os.listdir("modules") if m.endswith(".py") and os.path.isfile(f"modules/{m}")]


def update_module_table():
    global titles, module_table, descriptions, module_names, ids, module_table_data

    descriptions = []
    module_names = []
    ids = [str(i) for i in range(len(modules))]
    # populate arrays from /modules
    for module in modules:
        try:
            with open(f"modules/{module}", "r") as f:
                lines = f.read().split("\n")
                name_line, desc_line = lines[:2]  # metadata is first two lines -> change this to search for it in the file instead of being in the top two lines. maybe use regex? 
                module_names.append(name_line.split("# name: ")[1] if "# name: " in name_line else "<unnamed>")
                new_desc = desc_line.split("# description: ")[1] if "# description: " in desc_line else "<none>"
                descriptions.append(f"Description: {new_desc}")
        except FileNotFoundError:
            print(f"Could not access {module}: Not found in /modules")
        except PermissionError:
            print(f"Could not access {module}: Permission denied")

    module_table_data = [ids, module_names, descriptions]
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
    return modules[choice_index]


"""
All actions:
- Select a module
- Import module from file
- Import module from server
- Change settings
- Print user guide from modules
- Exit
"""

def action_select():
    actions = ["Select a module", "Import module from file", "Import module from server", "Change settings", "Print user guide", "Exit"]
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
        

def load_module(module: str):
    # load module
    spec = importlib.util.spec_from_file_location(module, f"modules/{module}")
    external_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external_module)

    # check if module has solver() function
    if hasattr(external_module, "solver"):
        external_module.solver()
    else:
        print(f"{module} does not have a solver() function.")


def change_settings():
    settings_table = table.Table(title="Settings")
    settings_table.add_column("Setting", justify="right", style="green")
    settings_table.add_column("Value", justify="left", style="yellow")
    for setting, value in settings.items():
        settings_table.add_row(setting, value)

    console.print(settings_table)
    choice = get_valid_input(f"> Select the setting you want to change by its {green}ID{reset} or {yellow}name{reset}: ", list(settings.keys()), True, err_word="setting")
    if choice == "\0":
        return
    settings[choice] = input(f"Enter the new value for {choice}: ")
    json.dump(settings, open("settings.json", "w"))


def main():
    os.system("cls" if os.name == "nt" else "clear")  # ps supports `clear` but this is here just in case

    while True:
        refresh_modules()
        update_settings()
        match action_select():
            case "Select a module":
                module = module_select()
                print(f"\n-----------[ {green}Start of {module} {reset}]-----------")
                load_module(module)
                print(f"------------[ {red}End of {module} {reset}]------------\n")
            case "Import module from file":
                print("not implemented yet")  # todo: prompt user with file input dialog thingy: adds slected file to /modules 
            case "Import module from server":
                print("not implemented yet")  # todo: prompt user with input dialog: get valid input (valid_inputs = modules.txt on server) -> download module from server -> add to /modules
            case "Change settings":  # possibly tag system? (settings + search)
                change_settings()
            case "Print user guide":
                print(tutorial_str)
            case "Exit":
                print("Exiting...")
                exit(0)

if __name__ == "__main__":
    main()
