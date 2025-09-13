from pathlib import Path
import csv

script_location = Path(__file__).resolve().parent
stats = Path("C:\Program Files\Steam\steamapps\common\FPSAimTrainer\FPSAimTrainer\stats")

def scenarios_played():
    pass

    # get all scenarios
    # write scores to text doc
    # record latest date
    # only record if file is later than latest date
    
def create_avasive_csv():
    fields = [
        'category',
        'subcategory',
        'easy',
        'med',
        'hard'
    ]
    categories = [
        'Tracking',
        'Switching',
        'Clicking'
    ]
    subcategories = [
        'Smooth',
        'Control',
        'Reactive',
        'Stability',
        'Evasive',
        'Speed',
        'Static',
        'Precise',
        'Elusive',
    ]
    mods = [
        'Easy', '', 'Hard'
    ]
    scenarios = [
        'FreightTrack',
        'Smoothsphere Glider',
        'Avasphere Intermediate',
        'Airva Control',
        'AvaTrack Ground Flicker',
        'cuteTrack',
        'SilkyTS',
        'TrixieSwitch',
        'AvomiTS',
        'avaSwitch',
        'Avasive Speed Switch',
        'AviaTS',
        'Avomi ww4t',
        'Avasive 1w3ts',
        'miaoClick',
        'B180 Avasive',
        'domiClick',
        'MadClick'
    ]
    len_cat = len(categories)
    len_subcat = len(subcategories)
    len_scen = len(scenarios)

    data = [None for _ in range(len_scen)]
    for i in range(len(scenarios)):
        category = categories[int(i / (len_scen / len_cat))]
        subcategory = subcategories[int(i / (len_scen / len_subcat))]
        scenario = scenarios[i]
        scenario_names = [f'{scenario}{f' {mod}' if mod!='' else ''}' for mod in mods]
        data[i] = [category, subcategory, *scenario_names]
    
    with open('avasive_s1.csv', 'w', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(fields)
        csvwriter.writerows(data)


    



if __name__ == "__main__":
    create_avasive_csv()
