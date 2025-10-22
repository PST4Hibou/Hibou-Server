from src.ptz.ui_controller import start_ui_controller
from src.settings import SETTINGS
from src.ptz.ptz import PTZ


def start_ptz_calibration():
    """
    Launch the PTZ calibration interface for manual adjustment.

    This function initializes a PTZ (Pan-Tilt-Zoom) camera client using
    connection settings from the `SETTINGS` object, and then opens the
    `start_ui_controller` GUI for manual PTZ control.

    Features of the GUI:
        - Move the camera using arrow buttons (up, down, left, right).
        - Adjust movement speed with + / − buttons.
        - Stop movement with the STOP button.
        - Monitor the current azimuth of the camera in real time.
        - Display a custom instructional message at the bottom.

    Calibration workflow:
        1. Use the GUI to adjust the PTZ camera until the desired azimuth is reached.
        2. Manually update the configuration file (e.g., `.env`) with the new azimuth value.
        3. Close the GUI to finish calibration.

    Notes:
        - Ensure the PTZ client is reachable and credentials in SETTINGS are correct.
        - The bottom text guides the user to manually update the configuration.
        - This function does not automatically save the new azimuth.

    Example usage:
        start_ptz_calibration()
    """
    ptz = PTZ(SETTINGS.PTZ_HOST, SETTINGS.PTZ_USERNAME, SETTINGS.PTZ_PASSWORD)

    start_ui_controller(
        ptz,
        "Once the correct azimuth has been found, please update .env conf file \n with the new value",
    )

    exit()
