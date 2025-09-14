import os
import dotenv
from pathlib import Path
import csv

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent
KOVAAKS_STATS=os.getenv("KOVAAKS_STATS_PATH")
KOVAAKS_STATS_PATH = Path(KOVAAKS_STATS)

def create_csv(
        name: str,
        fields:list[str],
        categories:list[str],
        subcategories:list[str],
        mods:list[str],
        scenarios:list[str]
    ):
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
    
    with open('%s.csv' % name, 'w', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(fields)
        csvwriter.writerows(data)

def create_voltaic_csv():
    fields = [
        'category',
        'subcategory',
        'easy',
        'med',
        'hard'
    ]
    categories = [
        'Clicking',
        'Tracking',
        'Switching',
    ]
    subcategories = [
        'Dynamic',
        'Static',
        'Linear',
        'Precise',
        'Reactive',
        'Control',
        'Speed',
        'Evasive',
        'Stability',
    ]
    mods = [
        'Novice S5', 'Intermediate S5', 'Advanced S5'
    ]
    scenarios = [
        'VT Pasu',
        'VT Popcorn',
        'VT 1w3ts',
        'VT ww5t',
        'VT Frogtagon',
        'VT Floating Heads',
        'VT PGT',
        'VT Snake Track',
        'VT Aether',
        'VT Ground',
        'VT Raw Control',
        'VT Controlsphere',
        'VT DotTS',
        'VT EddieTS',
        'VT DriftTS',
        'VT FlyTS',
        'VT ControlTS',
        'VT Penta Bounce',
    ]
    create_csv('voltaic_s5', fields, categories, subcategories, mods, scenarios)


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
    create_csv('avasive_s1', fields, categories, subcategories, mods, scenarios)


if __name__ == "__main__":
    # create_avasive_csv()
    create_voltaic_csv()
