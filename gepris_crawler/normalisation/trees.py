from ..data_transformations import is_reference, extract_institution_id, get_reference_path, get_reference_children, \
    get_reference_value, extract_id, remove_http_prefix
from ..gepris_helper import is_gepris_path

ORIGINAL_INST_SUBINSTITUTIONS_KEY = 'untergeordneteInstitutionen'
NORMALISED_INST_SUBINSTITUTIONS_KEY = 'normalised_subinstitutions'
ORIGINAL_INST_PROJECTS_KEY = 'projekteNachProgrammen'
NORMALISED_INST_PROJECTS_KEY = 'normalised_projects'

ORIGINAL_PERS_PROJECTS_KEY = 'projekteNachRolle'
NORMALISED_PERS_PROJECTS_KEY = 'normalised_projects'
ORIGINAL_PERS_PRICES_KEY = 'preise'
NORMALISED_PERS_PRICES_KEY = 'normalised_prices'


def normalise_sub_institutions(institutions):
    leaves = []
    for sub_inst in institutions:
        if is_reference(sub_inst):
            sub_inst_id = extract_institution_id(get_reference_path(sub_inst))
            if sub_inst_id is not None:
                sub_children = get_reference_children(sub_inst)
                # if we have no further sub children, just add the id to the list
                if sub_children is None:
                    leaves.append(sub_inst_id)
                # if we have further sub children, add a dict with a single entry to the list
                else:
                    leaves.append({sub_inst_id: normalise_sub_institutions(sub_children)})
            else:
                raise ValueError(f'Unexpected subinstitution, should include a institution path, but was {sub_inst}')
        else:
            raise ValueError(
                f'Unexpected subinstitution, should be a reference (path, name, [children])but was {sub_inst} in {institutions}')
    return leaves


def normalise_prices(price_categories):
    normalised_prices = {}
    for category in price_categories:
        if is_reference(category) and get_reference_children(category) is not None:
            prices = []
            for price in get_reference_children(category):
                if is_reference(price) and get_reference_children(price) is None:
                    price['path'] = remove_http_prefix(get_reference_path(price))
                    prices.append(price)
                else:
                    raise ValueError(f'Expected price to be reference without children but was: {price}')
            normalised_prices[get_reference_value(category)] = prices
        else:
            raise ValueError(f'Expect price category to be reference with children but was: {category}')
    return normalised_prices


def normalise_tree_leaves(entries, context_to_keep):
    leaves = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if is_reference(entry) \
                and get_reference_path(entry) is not None \
                and is_gepris_path(get_reference_path(entry), context_to_check=context_to_keep):
            # should not have children
            if get_reference_children(entry) is not None:
                raise ValueError(f'References in tree should not have children. But this one has: {entry}')
            element_id = extract_id(get_reference_path(entry))
            # if it's a searched context reference add the it to the list
            leaves.append(element_id)
        elif is_reference(entry) and get_reference_children(entry) is not None:
            name = get_reference_value(entry)
            children = get_reference_children(entry)
            # if the entry has children add a dict with the value and its normalised children to the list
            leaves.append({name: normalise_tree_leaves(children, context_to_keep)})
        elif isinstance(entry, list):
            entries.extend(entry)
        # ignore all other stuff (other context references, strings, etc.)
        i += 1
    return leaves

def normalise_institution_trees(institution_trees_dict):
    # check if any other trees are in there:
    unexpected_keys = set(institution_trees_dict.keys()) - {ORIGINAL_INST_PROJECTS_KEY,
                                                            ORIGINAL_INST_SUBINSTITUTIONS_KEY}
    if len(unexpected_keys) > 0:
        raise ValueError(f'There were unexpected trees on the page: {unexpected_keys}')

    # normalise subinstitutions
    sub_institutions = institution_trees_dict.get(ORIGINAL_INST_SUBINSTITUTIONS_KEY)
    if sub_institutions is not None:
        institution_trees_dict[NORMALISED_INST_SUBINSTITUTIONS_KEY] = normalise_sub_institutions(sub_institutions)
        del institution_trees_dict[ORIGINAL_INST_SUBINSTITUTIONS_KEY]
    # normalise projects
    projects = institution_trees_dict.get(ORIGINAL_INST_PROJECTS_KEY)
    if projects is not None:
        institution_trees_dict[NORMALISED_INST_PROJECTS_KEY] = normalise_tree_leaves(projects, 'projekt')
        del institution_trees_dict[ORIGINAL_INST_PROJECTS_KEY]

    return institution_trees_dict


def normalise_person_trees(person_trees_dict):
    # check if any other trees are in there:
    unexpected_keys = set(person_trees_dict.keys()) - {ORIGINAL_PERS_PROJECTS_KEY, ORIGINAL_PERS_PRICES_KEY}
    if len(unexpected_keys) > 0:
        raise ValueError(f'There were unexpected trees on the page: {unexpected_keys}')

    # normalise projects
    projects = person_trees_dict.get(ORIGINAL_PERS_PROJECTS_KEY)
    if projects is not None:
        person_trees_dict[NORMALISED_PERS_PROJECTS_KEY] = normalise_tree_leaves(projects, 'projekt')
        del person_trees_dict[ORIGINAL_PERS_PROJECTS_KEY]

    prices = person_trees_dict.get(ORIGINAL_PERS_PRICES_KEY)
    if prices is not None:
        person_trees_dict[NORMALISED_PERS_PRICES_KEY] = normalise_prices(prices)
        del person_trees_dict[ORIGINAL_PERS_PRICES_KEY]

    return person_trees_dict
