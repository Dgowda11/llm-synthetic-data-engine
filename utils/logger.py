import logging

import settings


def configure_logging() -> logging.Logger:
	"""Configure application logging and return the project logger."""
	level_name = settings.get_env("LOG_LEVEL", "INFO").upper()
	level = getattr(logging, level_name, None)
	if not isinstance(level, int):
		raise ValueError(
			"LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
		)

	logging.basicConfig(
		level=level,
		format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
	)
	return logging.getLogger("synthetic_data_engine")
