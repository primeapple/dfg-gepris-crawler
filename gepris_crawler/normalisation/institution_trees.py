from ..data_transformations import is_reference, extract_institution_id, get_reference_path

ORIGINAL_SUBINSTITUTIONS_KEY = 'untergeordneteInstitutionen'
NORMALISED_SUBINSTITUTIONS_KEY = 'normalised_subinstitutions'


def normalise_institutions(institutions):
    leaves = []
    for sub_inst in institutions:
        if is_reference(sub_inst):
            sub_inst_id = extract_institution_id(get_reference_path(sub_inst))
            if sub_inst_id is not None:
                sub_children = sub_inst.get('children')
                # if we have no further sub children, just add the integer to the list
                if sub_children is None:
                    leaves.append(sub_inst_id)
                # if we have further sub children, add a dict with a single entry to the list
                else:
                    leaves.append({sub_inst_id: normalise_institutions(sub_children)})
            else:
                raise ValueError(f'Unexpected subinstitution, should include a institution path, but was {sub_inst}')
        else:
            raise ValueError(f'Unexpected subinstitution, should be a reference (path, name, [children])but was {sub_inst} in {institutions}')
    return leaves


def add_normalised_subinstitution_tree(institution_trees_dict):
    if (sub_institutions := institution_trees_dict.get(ORIGINAL_SUBINSTITUTIONS_KEY)) is not None:
        institution_trees_dict[NORMALISED_SUBINSTITUTIONS_KEY] = normalise_institutions(sub_institutions)
    return institution_trees_dict
