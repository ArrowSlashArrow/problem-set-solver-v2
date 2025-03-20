import os
from rich import console, table

# intialize rich console and module table arrays
console = console.Console()
modules = os.listdir("modules")

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
def new_table(titles: dict, rows: list[list]):
    module_table = table.Table()
    for title, formatting in titles.items():
        module_table.add_column(title, justify=formatting["justify"], style=formatting["style"])
    for vals in zip(*rows):
        module_table.add_row(*vals)
    return module_table


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
        with open(f"modules/{module}", "r") as f:
            name_line, desc_line = f.read().split("\n")[:2]  # metadata is first two lines
            module_names.append(name_line.split("# name: ")[1] if "# name: " in name_line else "<unnamed>")
            new_desc = desc_line.split("# description: ")[1] if "# description: " in desc_line else "<none>"
            descriptions.append(f"Description: {new_desc}")

    module_table_data = [ids, module_names, descriptions]
    module_table = new_table(titles, module_table_data)
    # generate table at execution time to account for imported modules
    console.print(module_table)
    
    choice = 0
    # prompt until valid input
    while True:
        inp = input("> Select a module by name or number: ").rstrip()
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
- Export settings to file
- Print user guide
- Exit
"""

def action_select():
    actions = ["Select a module", "Import module", "Change settings", "Export settings to file", "Print user guide", "Exit"]
    ids = [str(i) for i in range(len(actions))]
    titles = {
        "ID": {"style": "green", "justify": "right"},
        "Action": {"style": "yellow", "justify": "right"}
    }
    action_table_data = [ids, actions]
    action_table = new_table(titles, action_table_data)
    console.print(action_table)
    choice = ""
    while True:
        inp = parse_num(input("> Select an action by its ID: ").rstrip())
        if type(inp) != int:
            if inp not in ids:
                print(f"{inp} is not an available action, please try again.")
                continue
            choice = inp
        if inp < 0 or inp >= len(actions):
            print(f"{inp} is out of range of the choice IDs, please try again.")
            continue
        choice = actions[inp]
        break
    return choice
        

def main():
    os.system("cls" if os.name == "nt" else "clear")

    while True:
        match action_select():
            case "Select a module":
                module = module_select()
                print("selected " + module)  # temp
            case "Import module":
                print("not implemented yet")  # todo: prompt user with file input dialog thingy
            case "Change settings":
                print("not implemented yet")  # todo: print box with all settings and values, get user input as id or str, prompt for new value
            case "Export settings to file":
                print("not implemented yet")  # todo: copy settings.json to a new file with unix timestamp (settings-<timestamp>.json)
            case "Print user guide":
                print("not implemented yet")  # todo: print user guide (string with formatting)
            case "Exit":
                print("Exiting...")
                exit(0)

if __name__ == "__main__":
    main()