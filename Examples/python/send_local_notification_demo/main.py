#!/usr/bin/env python3

"""
Local Notification Demo shows how to send notification to your LaMetric Time in local network
"""

from enum import Enum
import json
import requests

__author__ = "Dmytro Baryskyy"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "dmytro@lametric.com"


# =============================== Customization area =====================================
LAMETRIC_TIME_IP_ADDRESS = "<ip_address_of_lametric_time>"
LAMETRIC_TIME_API_KEY = "<your_api_key>"
# ========================================================================================


class Priority(Enum):
    info = "info",
    warning = "warning"
    critical = "critical"


class Sound (dict):
    """ Represents notification sound """
    def __init__(self, sound, repeat=1):
        """
        Constructor
        :param sound: Sound id, full list can be found at
            http://lametric-documentation.readthedocs.io/en/latest/reference-docs/device-notifications.html
        :param repeat: Sound repeat count, if set to 0 sound will be played until notification is dismissed
        """
        dict.__init__({})
        self["category"] = "notifications"
        self["id"] = sound
        self["repeat"] = repeat
        return


class Frame (dict):
    """ Represents single frame. Frame can display icon and text. """

    def __init__(self, icon, text):
        """
        Constructor
        :param icon: icon id in form of "iXXX" for static icons, or "aXXXX" for animated ones.
        :param text: text message to be displayed
        """
        dict.__init__({})
        if icon is not None:
            self["icon"] = icon
        self["text"] = text


class Notification (dict):
    """ Represents notification message """
    def __init__(self, priority, frames, sound):
        """
        Constructor
        :param priority: notification priority, Priority enum.
        :param frames: list of Frame objects
        :param sound: Sound object
        """
        dict.__init__({})
        self["priority"] = priority.name
        self["model"] = {
            "frames": frames,
            "sound" : sound
        }
        return


class LaMetricTime:
    """
    Allows to send notification to your LaMetric Time device in local network
    """
    def __init__(self, ip_address, port, api_key):
        """
        Constructor
        :param ip_address: IP address of the LaMetric Time
        :param port: 8080 for insecure connection or 4343 for secure one
        :param api_key: device API key
        """
        self.notifications_url = "https://{0}:{1}/api/v2/device/notifications".format(ip_address, port)
        self._api_key = api_key
        return

    def send(self, notification):
        """
        Sends notification to LaMetric Time
        :param notification: instance of Notification class
        :return: (status_code, body)
        """
        r = requests.post(self.notifications_url, json=notification, auth=('dev',self._api_key), verify=False)
        return r.status_code, r.text


if __name__ == "__main__":
    # Creating notification with text "LaMetric", "time", "is", "great" on different frames and sound
    # And on the last frame we add fireworks animation (can be found at https://developer.lametric.com/icons)
    # Full list of sounds can be found here
    #   http://lametric-documentation.readthedocs.io/en/latest/reference-docs/device-notifications.html
    notification = Notification(Priority.info,
                                frames=[Frame(icon=None, text="LaMetric"),
                                        Frame(icon=None, text="time"),
                                        Frame(icon=None, text="is"),
                                        Frame(icon="a2867", text="Great!")],
                                sound=Sound("positive4"))

    # IP address can be found in LaMetric Time app -> Settings -> Wi-Fi
    # API Key can be found in your developer account at https://developer.lametric.com/user/devices
    lametric_time = LaMetricTime(LAMETRIC_TIME_IP_ADDRESS,
                                 port=4343,
                                 api_key=LAMETRIC_TIME_API_KEY)

    print("Sending: {0} \nto {1}".format(json.dumps(notification), lametric_time.notifications_url))
    # Sending notification
    status_code, body = lametric_time.send(notification)
    # Printing result
    print("{0}:{1}".format(status_code, body))
