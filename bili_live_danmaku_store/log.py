import logging
import sys


def configure_logger(logger: logging.Logger, filename_stem: str):
    """
    Deletes **all** existing handlers of `logger`, and adds following handlers:

    - `{filename_stem}.log` (INFO)
    - `{filename_stem}.debug.log` (DEBUG)
    - `sys.stdout` (INFO)
    """
    logger.handlers = []

    logger.setLevel(logging.DEBUG)

    log_file_formatter = logging.Formatter(
        style="{",
        fmt="[{name} {asctime} {levelname}]@{thread}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log_stdout_formatter = logging.Formatter(
        style="{",
        fmt="[{name} {asctime} {levelname}]@{thread}: {message}",
        datefmt="%m-%d %H:%M:%S",
    )

    log_file_handler = logging.FileHandler(
        filename=f"{filename_stem}.log", encoding="utf-8"
    )
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(log_file_formatter)

    log_debug_file_handler = logging.FileHandler(
        filename=f"{filename_stem}.debug.log", encoding="utf-8"
    )
    log_debug_file_handler.setLevel(logging.DEBUG)
    log_debug_file_handler.setFormatter(log_file_formatter)

    log_stdout_handler = logging.StreamHandler(sys.stdout)
    log_stdout_handler.setLevel(logging.INFO)
    log_stdout_handler.setFormatter(log_stdout_formatter)

    logger.addHandler(log_file_handler)
    logger.addHandler(log_debug_file_handler)
    logger.addHandler(log_stdout_handler)
