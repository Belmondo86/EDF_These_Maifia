"""
Abaqus INP Parameter Sweep Generator

This script generates Abaqus (.inp) input files by systematically varying
the thermal properties of three materials.

Materials:
    ASP : Asphalt
    EPD : EPDM
    RES : Resin

Thermal Properties:
    RHO : Density
    CP  : Specific Heat Capacity
    K   : Thermal Conductivity
    HFL : Heat Flux
    EMS : Emissivity

Parameter Sweep Modes:
    mode = 0 (OFAT - One-Factor-At-a-Time):
        Varies one parameter at a time while keeping all others constant.

    mode = 1 (Grid Search - Full Factorial):
        Generates all possible combinations of parameter values.

Output:
    Generates Abaqus (.inp) files in "Generated_inp" with parameter values
    embedded in both content and filenames. OFAT mode varies one parameter
    at a time, while grid search generates all combinations.
"""

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from pathlib import Path
from itertools import product
import os
# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
work_path = r'H:\Guarda_database'
os.chdir(work_path) # change the current directory to the work_path


######

mode = 0  # 0 = One Factor At a Time, 1 = Grid Search

# --------------------------------------------------
# PARAMETER RANGE GENERATION
# --------------------------------------------------

# generate numeric values with controlled precision.
def generate_range(start, end, step, precision):

    values = [] # list that will store the generated values of the parameter range
    current = start

    while current <= end:
        values.append(round(current, precision))
        current += step

    return values

# --------------------------------------------------
# PARAMETER AUTOMATION
# --------------------------------------------------

# automatically build the parameter dictionary
def build_parameters():

    material_ranges = {

        "ASP": {
            "RHO": (2381, 2581, 50, 0),
            "CP":  (819, 919, 25, 0),
            "K":   (1.16, 3.16, 0.5, 3),
            "HFL": (434, 634, 50, 0),
            "EMS": (0.9, 1.0, 0.025, 3)
        },

        "EPD": {
            "RHO": (1015, 1115, 25, 0),
            "CP":  (1914, 2114, 50, 0),
            "K":   (0.184, 0.384, 0.05, 3),
            "HFL": (509, 909, 100, 0),
            "EMS": (0.9, 1.0, 0.025, 3)
        },

        "RES": {
            "RHO": (1030, 1130, 25, 0),
            "CP":  (1867, 1967, 25, 0),
            "K":   (0.114, 0.314, 0.05, 3),
            "HFL": (508, 908, 100, 0),
            "EMS": (0.85, 1.0, 0.0375, 4)
        }

    }
    # dictionary creation
    parameters = {
        f"{mat}_{prop}": generate_range(*ranges) # 3 - create a parameter name = placeholders. * unpacks the tuple so ranges become arguments for the function
        for mat, props in material_ranges.items() # 1 - iterate through materials. Returns key(material) and value (properties)
        for prop, ranges in props.items() # 2 - iterate through properties of that material. Return key(prop) and value(ranges). Mat->props->prop
    }

    return parameters

# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------

def main():

    parameters = build_parameters()

    # load template
    template_path = Path("inp_template.inp") # path to inp_template file

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # output directory
    output_dir = Path("1_inp_list") # path to Generated_inp folder

    try:
        output_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Error creating directory: {e}")

    parameter_names = list(parameters.keys()) # parameter list
    value_lists = list(parameters.values()) # value list

    counter = 1 # iteration (file number)

    # --------------------------------------------------
    # MODE 0 → ONE PARAMETER AT A TIME
    # --------------------------------------------------

    if mode == 0:

        # baseline values (first value of each parameter)
        baseline = {p: parameters[p][0] for p in parameter_names} # e.g. asp_rho: 2200, ; asp_cp: 800, ; asp_k:0.7

        for param in parameter_names: # one parameter per time = parameters loop e.g. asp_rho

            for value in parameters[param]: # iteration through all values of that parameter = values loop e.g. all possible values

                current_values = baseline.copy() # create a baseline copy to modify
                current_values[param] = value # update value

                new_text = template # template copy

                for key, val in current_values.items():
                    new_text = new_text.replace(f"{{{{{key}}}}}", str(val)) # replace placeholders

                # filename: ID + parameter being varied + value

                file_name = output_dir / f"ID_{counter:03d}_{param}_{value}.inp"

                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(new_text)

                counter += 1

    # --------------------------------------------------
    # MODE 1 → FULL GRID SEARCH
    # --------------------------------------------------

    if mode == 1:

        for combination in product(*value_lists):

            current_values = dict(zip(parameter_names, combination)) # combination turns to a dictionary

            new_text = template

            for key, value in current_values.items():
                new_text = new_text.replace(f"{{{{{key}}}}}", str(value))

            # filename (only ID)
            file_name = output_dir / f"ID_{counter:03d}.inp"

            with open(file_name, "w", encoding="utf-8") as f:
                f.write(new_text)

            counter += 1

    print(f"{counter - 1} files generated in {output_dir}")

# --------------------------------------------------
# SCRIPT ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
