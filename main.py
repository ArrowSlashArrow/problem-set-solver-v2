import os
from rich import console, table

# intialize rich console and module table arrays
console = console.Console()
modules = os.listdir("modules")
descriptions = []
module_names = []

# maybe put this inside of new_table()
# populate arrays from /modules
for module in modules:
    with open(f"modules/{module}", "r") as f:
        lines = f.read().split("\n")
        name_line = lines[0]
        desc_line = lines[1]
        module_names.append(name_line.split("# name: ")[1] if "# name: " in name_line else "<unnamed>")
        descriptions.append(desc_line.split("# description: ")[1] if "# description: " in desc_line else "<none>")

# table init
module_table = table.Table(title="Installed Modules")
module_table.add_column("ID", justify="right", style="cyan")
module_table.add_column("Module Name", justify="right", style="green")
module_table.add_column("Module Description", justify="left", style="yellow")

# table rows
[module_table.add_row(row[0], row[1], f"Description: {row[2]}") for row in zip([str(i) for i in range(len(modules))], module_names, descriptions)]

# parse num util function
def parse_num(num):
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return num

# returns module filename
def module_select():
    console.print(module_table)
    choice = 0
    # prompt until valid input
    while True:
        inp = input("> Select a module by name or number: ")
        parsed_inp = parse_num(inp)
        if type(parsed_inp) == int:
            if parsed_inp < 0 or parsed_inp > len(module_names):
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


def main():
    os.system("cls" if os.name == "nt" else "clear")
    # todo: action select screen
    module = module_select() 
    print("selected " + module)  # temporary


if __name__ == "__main__":
    main()