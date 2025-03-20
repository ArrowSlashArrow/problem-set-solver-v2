import os, importlib.util
from rich import console, table

# intialize rich console and module table arrays
console = console.Console()
modules = []

# ansi colours
reset = "\x1b[0m"
cyan = "\x1b[38;5;6m"
green = "\x1b[38;5;2m"
yellow = "\x1b[38;5;3m"
red = "\x1b[38;5;9m"

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


def refresh_modules():
    global modules
    modules = [m for m in os.listdir("modules") if m.endswith(".py")]

# returns module filename
def module_select():
    titles = {
        "ID": {"style": "cyan", "justify": "right"},
        "Module Name": {"style": "green", "justify": "right"},
        "Module Description": {"style": "yellow", "justify": "left"}
    }

    descriptions = []
    module_names = []
    ids = [str(i) for i in range(len(modules))]
    # populate arrays from /modules
    for module in modules:
        try:
            with open(f"modules/{module}", "r") as f:
                name_line, desc_line = f.read().split("\n")[:2]  # metadata is first two lines -> change this to search for it in the file instead of being in the top two lines. maybe use regex? 
                module_names.append(name_line.split("# name: ")[1] if "# name: " in name_line else "<unnamed>")
                new_desc = desc_line.split("# description: ")[1] if "# description: " in desc_line else "<none>"
                descriptions.append(f"Description: {new_desc}")
        except FileNotFoundError:
            print(f"Could not access {module}: Not found in /modules")
        except PermissionError:
            print(f"Could not access {module}: Permission denied")

    module_table_data = [ids, module_names, descriptions]
    module_table = new_table("Installed Modules", titles, module_table_data)
    # generate table at execution time to account for imported modules
    console.print(module_table)
    
    choice = 0
    # prompt until valid input
    while True:
        inp = input(f"> Select a module by {cyan}ID{reset} or {green}name{reset}: ").rstrip()
        parsed_inp = parse_num(inp)
        if type(parsed_inp) == int:
            if parsed_inp < 0 or parsed_inp >= len(module_names):
                console.print("Invalid number, please try again.")
                continue
            else:
                choice = module_names[parsed_inp]
                break
        else:
            if inp not in module_names:
                console.print("Invalid module name, please try again.")
                continue
            else:
                choice = inp
                break
    choice_index = module_names.index(choice)
    return modules[choice_index]


"""
All actions:
- Select a module
- Import module
- Change settings
- Print user guide
- Exit
"""

def action_select():
    actions = ["Select a module", "Import module", "Change settings", "Print user guide", "Exit"]
    lower_actions = [a.lower() for a in actions]
    ids = [str(i) for i in range(len(actions))]
    titles = {
        "ID": {"style": "green", "justify": "right"},
        "Action": {"style": "yellow", "justify": "left"}
    }
    action_table_data = [ids, actions]
    action_table = new_table("Actions", titles, action_table_data)
    console.print(action_table)
    choice = ""
    while True:
        inp = parse_num(input(f"> Select an action by its {green}ID{reset} or {yellow}name{reset}: ").rstrip())
        # choice is a name
        if type(inp) != int:
            # choice is not in action array
            if inp.lower() not in lower_actions:
                print(f"{inp} is not an available action, please try again.")
                continue
            else: # valid input
                choice = actions[lower_actions.index(inp.lower())]
                break
        # choice is a number
        if inp < 0 or inp >= len(actions):
            # out of range
            print(f"{inp} is out of range of the choice IDs, please try again.")
            continue
        else:
            choice = actions[inp]
            break
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

def main():
    os.system("cls" if os.name == "nt" else "clear")  # ps supports `clear` but this is here just in case

    while True:
        refresh_modules()
        match action_select():
            case "Select a module":
                module = module_select()
                print(f"\n-----------[ {green}Start of {module} {reset}]-----------")
                load_module(module)
                print(f"------------[ {red}End of {module} {reset}]------------\n")
            case "Import module":
                print("not implemented yet")  # todo: prompt user with file input dialog thingy: adds slected file to /modules or from a list of modules uploaded to server (kind of like pip)
            case "Change settings":  # possibly tag system? (settings + search)
                print("not implemented yet")  # todo: print box with all settings and values, get user input as id or str, prompt for new value
            case "Print user guide":
                print("not implemented yet")  # todo: print user guide (string with formatting)
            case "Exit":
                print("Exiting...")
                exit(0)

if __name__ == "__main__":
    main()