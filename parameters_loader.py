"""Centralize all the loading of data  from external files that are not in the ship file

Contains default path for those files
files in json format
"""
import json
import logging
import pathlib
import jsonschema
import appdirs
import schemas

summary = logging.getLogger("Summary")
details = logging.getLogger("Details")

APP_CONFIG = pathlib.Path(appdirs.user_data_dir("Drafnought")).joinpath("app_config.json")

DEFAULT_APP_CONFIG = {
    "last_file_path" : "",
    "max_points_in_structure":21
    }

def read_json(path, json_schema, default_data):
    """Read a json file and validate it against a schema

    If an exception occurs, the default data is returned
    Args:
        path (string): path to json file
        json_schema (dict) a dict with the json schema info
        default_data (dict): what should be returned in case of failure
    returns:
        a dict with the json data if everything works fine, default_data if not
    """
    try:
        summary.debug("loading parameter file %s", pathlib.Path(path).name)
        with open(path) as file:
            json_data = json.load(file)
    except OSError as error:
        summary.warning("Could not load file: %s\nLoading default values instead",
                        pathlib.Path(path).resolve())
        details.warning("Could not load file: %s\n%s",
                        pathlib.Path(path).resolve(), error)
        return default_data
    except json.JSONDecodeError as error:
        summary.warning("This file is not valid json: %s\nLoading default values instead",
                        pathlib.Path(path).resolve())
        details.warning("This file is not valid json: %s\n%s\n\nLoading default values instead",
                        pathlib.Path(path).resolve(), error)
        return default_data

    try:
        jsonschema.validate(json_data, json_schema)
    except jsonschema.ValidationError as error:
        summary.warning("Valid JSON but invalid Schema in: %s\nLoading default values instead",
                        path)
        details.warning("Valid JSON but invalid Schema in: %s\n%s", path, error)
        return default_data

    return json_data

def read_app_param():
    """build the data for the program config

    If the config file is not found, default values are used and an info-level message is logged

    Returns (dict):
        a dict with all the data
    """
    try:
        with open(APP_CONFIG) as file:
            param = json.load(file)
    except OSError as error:
        summary.warning("Could not load file: %s\n%s\nDefault values used",
                        APP_CONFIG.resolve(), error)
        return DEFAULT_APP_CONFIG
    except json.JSONDecodeError as error:
        summary.warning("Could not decode file: %s\n%s\nDefault values used",
                        APP_CONFIG.resolve(), error)
        return DEFAULT_APP_CONFIG

    for config, value in DEFAULT_APP_CONFIG.items():
        if config not in param.keys():
            param[config] = value
            summary.error("Missing definition %s from file %s", config, APP_CONFIG.resolve())
    return param

class Parameters:
    """Main class that contains all the parameters

    Attributes:
        hulls_shapes (dict): for each ship type, a list of lines that define the hull outer line.
            each line is a list of tuples (x, y) in relative coordinates
        ships_hlengths (dict): for each ship type, a dict {int:int} used to get the length
            from origin to bow
            The key is the biggest tonnage for which the length is still valid
            the value is the distance from origin to bow in funnel coordinates.
        app_config (dict): program configuration
    """
    def __init__(self):

        self.app_config = read_app_param()
        self.hulls_shapes = read_json("hull_shapes.json",
                                      schemas.HULLS_SHAPES_SCHEMA,
                                      schemas.DEFAULT_HULLS_SHAPES)
        self.turrets_positions = read_json("turrets_positions.json",
                                           schemas.TURRETS_POSITION_SCHEMA,
                                           schemas.DEFAULT_TURRETS_POSITION)
        self.turrets_scale = read_json("turrets_scale.json",
                                       schemas.TURRETS_SCALE_SCHEMA,
                                       schemas.DEFAULT_TURRETS_SCALE)
        self.turrets_outlines = read_json("turrets_outlines.json",
                                          schemas.TURRETS_OUTLINE_SCHEMA,
                                          schemas.DEFAULT_TURRETS_OUTLINE)
        raw_hlengths = read_json("lengths.json",
                                 schemas.HALF_LENGTHS_SCHEMA,
                                 schemas.DEFAULT_HALF_LENGTHS)

        self.ships_hlengths = {}
        for ship_type, lengths_dicts in raw_hlengths.items():
            self.ships_hlengths[ship_type] = convert_str_key_to_int(lengths_dicts)

    def write_app_param(self, new_parameters=None, file_path=None):
        """write the application config to a file

        Args:
            new_parameters (dict): new set of parameters to write.
                If not given, the current parameters are written.
            file_path (str): path to the file that should be created or overwritten.
                If not given, the default file path is used.
        """
        if file_path is None:
            file_path = APP_CONFIG.resolve()
        if new_parameters is None:
            new_parameters = self.app_config
        try:
            details.info("Saving app parameters to %s", file_path)
            pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as file:
                json.dump(new_parameters, file)
                details.info("Saved app parameters to %s", file_path)
        except OSError as error:
            summary.warning("Could not save app config file to: %s", file_path)
            details.warning("Could not save app config file to: %s\n%s", file_path, error)

def convert_str_key_to_int(data):
    """in a dictionary, convert to int the keys (assumed to be an int) that can be parsed to int
    AND order the dict in increasing key value

    the keys that cant be parsed are kept intact, but sorting still happens

    Args:
        data: anything.
        If it is not a dict, nothing is done and the returned value is identical the parameter

    Returns.
        An ordered dict with int keys if the param was a dict and the keys could be parsed to int,
        the same as the parameter if not
    """
    if isinstance(data, dict):
        new_dict = {}
        could_be_parsed = True
        for key, value in data.items():
            try:
                newk = int(key)
            except ValueError:
                could_be_parsed = False
                break
            new_dict[newk] = value
        if could_be_parsed:
            return new_dict
    return data
