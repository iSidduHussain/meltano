import logging
import requests
import uuid
import yaml

from typing import Dict

REQUEST_TIMEOUT = 2.0
MELTANO_TRACKING_ID = "UA-132758957-3"
MEASUREMENT_PROTOCOL_URI = "https://www.google-analytics.com/collect"
DEBUG_MEASUREMENT_PROTOCOL_URI = "https://www.google-analytics.com/debug/collect"


class GoogleAnalyticsTracker:
    def __init__(
        self,
        project,
        tracking_id: str = None,
        client_id: str = None,
        request_timeout: float = None,
    ) -> None:
        self.project = project
        self.tracking_id = tracking_id or MELTANO_TRACKING_ID
        self.request_timeout = request_timeout or REQUEST_TIMEOUT

        config = self.project_config()
        self.send_anonymous_usage_stats = (
            config.get("send_anonymous_usage_stats", False) == True
        )

        self.client_id = client_id or self.project_id()

    def project_config(self) -> Dict:
        """Fetch the project config from the root directory."""
        config_file = self.project.root.joinpath("project_config.yml")
        if config_file.is_file():
            with config_file.open() as file:
                config = yaml.load(file) or {}
        else:
            config = {}

        return config

    def update_permission_to_track(self, send_anonymous_usage_stats: bool) -> None:
        """Update the send_anonymous_usage_stats in the project config."""
        config = self.project_config()
        config["send_anonymous_usage_stats"] = send_anonymous_usage_stats

        config_file = self.project.root.joinpath("project_config.yml")
        with open(config_file, "w") as f:
            f.write(yaml.dump(config, default_flow_style=False))

    def project_id(self) -> None:
        """
        Fetch the project_id from the project config file.

        If it is not found (e.g. first time run), generate a valid uuid4 and
        store it in the project config file.
        """
        config = self.project_config()

        try:
            project_id_str = config.get("project_id", None) or ""
            project_id = uuid.UUID(project_id_str, version=4)
        except ValueError:
            project_id = uuid.uuid4()

            if self.send_anonymous_usage_stats:
                # If we are set to track Anonymous Usage stats, also store
                #  the generated project_id back to the project config file
                #  so that it persists between meltano runs.
                config["project_id"] = str(project_id)

                config_file = self.project.root.joinpath("project_config.yml")
                with open(config_file, "w") as f:
                    f.write(yaml.dump(config, default_flow_style=False))

        return project_id

    def event(self, category: str, action: str) -> Dict:
        """Constract a GA event with all the required parameters."""
        event = {
            "v": "1",
            "tid": self.tracking_id,
            "cid": self.client_id,
            "ds": "meltano cli",
            "t": "event",
            "ec": category,
            "ea": action,
        }
        return event

    def track_data(self, data: Dict, debug: bool = False) -> None:
        """Send usage statistics back to Google Analytics."""
        if self.send_anonymous_usage_stats == False:
            # Only send anonymous usage stats if you have explicit permission
            return

        if debug:
            tracking_uri = DEBUG_MEASUREMENT_PROTOCOL_URI
        else:
            tracking_uri = MEASUREMENT_PROTOCOL_URI

        try:
            r = requests.post(tracking_uri, data=data, timeout=self.request_timeout)

            if debug:
                logging.debug("GoogleAnalyticsTracker.track_data:")
                logging.debug(data)
                logging.debug("Response:")
                logging.debug(f"status_code: {r.status_code}")
                logging.debug(r.text)
        except requests.exceptions.Timeout:
            logging.debug("GoogleAnalyticsTracker.track_data: Request Timed Out")
        except requests.exceptions.ConnectionError as e:
            logging.debug("GoogleAnalyticsTracker.track_data: ConnectionError")
            logging.debug(e)
        except requests.exceptions.RequestException as e:
            logging.debug("GoogleAnalyticsTracker.track_data: RequestException")
            logging.debug(e)

    def track_event(self, category: str, action: str, debug: bool = False) -> None:
        event = self.event(category, action)
        self.track_data(event, debug)

    def track_meltano_init(self, project_name: str, debug: bool = False) -> None:
        event = self.track_event(
            category="meltano init", action=f"meltano init {project_name}", debug=debug
        )

    def track_meltano_add(
        self, plugin_type: str, plugin_name: str, debug: bool = False
    ) -> None:
        event = self.track_event(
            category=f"meltano add {plugin_type}",
            action=f"meltano add {plugin_type} {plugin_name}",
            debug=debug,
        )

    def track_meltano_discover(self, plugin_type: str, debug: bool = False) -> None:
        event = self.track_event(
            category="meltano discover",
            action=f"meltano discover {plugin_type}",
            debug=debug,
        )

    def track_meltano_elt(
        self, extractor: str, loader: str, transform: str, debug: bool = False
    ) -> None:
        event = self.track_event(
            category="meltano elt",
            action=f"meltano elt {extractor} {loader} --transform {transform}",
            debug=debug,
        )
