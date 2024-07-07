import math
import datetime

from libsonyapi.camera import Camera
from libsonyapi.actions import Actions


class Parameter:
    def __init__(self, name, value, index):
        self.name = name
        self.value = value
        self.index = index


class ExposureSettings:

    def __init__(self, shutter_spead: Parameter, iso: Parameter, f_value: Parameter, ev: float):
        self.shutter_spead = shutter_spead
        self.iso = iso
        self.f_value = f_value
        self.ev = ev


START_RECORDING_DATETIME = datetime.datetime(2024, 7, 7, 19, 0, 0, 0)
FINISH_RECORDING_DATETIME = datetime.datetime(2024, 7, 8, 7, 0, 0, 0)
INTERVAL = 15  # sec
ESTIMATED_MB_SIZE_OF_PHOTO = 70

# Make bigger for darker scenes for brighter effect
START_SHUTTER_SPEED = 1/1250
LIMIT_SHUTTER_SPEED = 10

# Make bigger for darker scenes for brighter effect
START_F_VALUE = 4
LIMIT_F_VALUE = 6

# Make lower for darker scenes for brighter effect
START_ISO = 3200

SUPPORTED_SHUTTER_SPEEDS=[]
SUPPORTED_F_VALUES=[]
SUPPORTED_ISO=[]

PEAK_EV = None
PEAK_EV_START = datetime.datetime(2024, 7, 7, 19, 0, 0, 0)
PEAK_EV_FINISHED = datetime.datetime(2024, 7, 8, 7, 0, 0, 0)

CURRENT_SETTINGS = None  # TO DO: Fill settings on start


def calculate_number_of_photos() -> None:
    seconds_of_shooting = (FINISH_RECORDING_DATETIME - START_RECORDING_DATETIME).seconds
    number_of_photos = seconds_of_shooting / INTERVAL
    estimated_size = number_of_photos * ESTIMATED_MB_SIZE_OF_PHOTO

    message = f"""
        START RECORDING ON: {START_RECORDING_DATETIME}
        FINISH RECORDING ON: {FINISH_RECORDING_DATETIME}
        NUMBER OF PHOTOS: {number_of_photos}
        ESTIMATED SIZE: {estimated_size} MB ({estimated_size / 1024} GB)
    """

    print(message)


def check_if_params_supported() -> None:
    if START_SHUTTER_SPEED not in SUPPORTED_SHUTTER_SPEEDS:
        raise Exception("Starting shutter speed is not available in your camera or with current settings")
    if LIMIT_SHUTTER_SPEED not in SUPPORTED_SHUTTER_SPEEDS:
        raise Exception("Shutter speed limit is not available in your camera or with current settings")

    if START_F_VALUE not in SUPPORTED_F_VALUES:
        raise Exception("Starting F Value is not available in your camera or with current settings")
    if LIMIT_F_VALUE not in SUPPORTED_F_VALUES:
        raise Exception("F Value limit is not available in your camera or with current settings")

    if START_ISO not in SUPPORTED_F_VALUES:
        raise Exception("Starting ISO is not available in your camera or with current settings")

    if LIMIT_SHUTTER_SPEED > INTERVAL:
        raise Exception("Shutter speed is longer than interval")


def fetch_supported_values(camera : Camera):
    global SUPPORTED_F_VALUES
    SUPPORTED_F_VALUES = camera.do(Actions.getAvailableFNumber)

    global SUPPORTED_SHUTTER_SPEEDS
    SUPPORTED_SHUTTER_SPEEDS = camera.do(Actions.getAvailableShutterSpeed)

    global SUPPORTED_ISO
    SUPPORTED_SHUTTER_SPEEDS = camera.do(Actions.getAvailableIsoSpeedRate)


def calculate_ev(f_value: float, iso: int, shutter_spead: float) -> float:
    # https://www.omnicalculator.com/other/exposure
    return math.log(
        ((100 * (pow(f_value, 2))) / (iso * shutter_spead)),
        2
    )


def calculate_ev_transitions():
    border_ev = calculate_ev(START_F_VALUE, START_ISO, START_SHUTTER_SPEED)
    settings_range = helper_function_generate_params_for_ev(border_ev, PEAK_EV)
    for ev, setting in settings_range.items():
        message = f"""
            EV: {ev}
            F: {setting.f_value}
            Shutter: {setting.shutter_spead}
            ISO: {setting.iso}
        """
        print(message)


def helper_function_generate_params_for_ev(border_ev, peak_ev):
    decreasing = border_ev > peak_ev

    current_ev = border_ev

    current_f = START_F_VALUE
    current_f_index = 0
    current_shutter = START_SHUTTER_SPEED
    current_shutter_index = 0
    current_iso = START_ISO
    current_iso_index = 0

    ev_list = {}

    latest_change = "f_value"

    while current_ev < peak_ev:
        if latest_change is not "shutter_spead" and current_shutter != LIMIT_SHUTTER_SPEED:
            current_shutter_index = current_shutter_index + 1 if decreasing else current_shutter_index - 1
            current_shutter = SUPPORTED_SHUTTER_SPEEDS[current_shutter_index]
            latest_change = "shutter_spead"
        elif latest_change is not "f_value" and current_f != LIMIT_F_VALUE:
            current_f_index = current_f_index + 1 if decreasing else current_f_index - 1
            current_f = SUPPORTED_F_VALUES[current_f_index]
            latest_change = "f_value"
        else:
            current_iso_index = current_iso_index - 1 if decreasing else current_iso_index + 1
            current_iso = SUPPORTED_ISO[current_iso_index]
            latest_change = "iso"
        current_ev = calculate_ev(current_f, current_iso, current_shutter)
        new_settings = ExposureSettings(
            Parameter("ShutterSpead", current_shutter, current_shutter_index),
            Parameter("ISO", current_iso, current_iso_index),
            Parameter("FValue", current_f, current_f_index),
            current_ev
        )
        ev_list[current_ev] = new_settings

    print(ev_list)

    return ev_list







if __name__ == "__main__":
    camera = Camera()
    check_if_params_supported()
    fetch_supported_values(camera)
    calculate_number_of_photos()
    calculate_ev_transitions()

