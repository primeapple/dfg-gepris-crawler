from ..custom_exceptions import UnexpectedFieldError


def normalise_attributes(unstructured_attributes_dict, loader, attributes_map, keys_to_process={}, keys_to_remove={}):
    for key, value in unstructured_attributes_dict.items():
        normalised_key = attributes_map.get(key)
        if normalised_key is None:
            raise UnexpectedFieldError(f'Unknown attribute key found: "{key}", make sure to add it to the corresponding ATTRIBUTES_MAP')
        elif normalised_key in keys_to_process:
            processed = keys_to_process[normalised_key](value)
            for processed_key, processed_val in processed.items():
                loader.add_value(processed_key, processed_val)
        elif normalised_key in keys_to_remove:
            pass
        else:
            loader.add_value(normalised_key, value)
    return loader.load_item()
