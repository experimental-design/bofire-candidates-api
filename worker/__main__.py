import logging
import os

from client import Client

from worker import Worker


def setup_logging(log_level: str):
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    log_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    try:
        selected_log_level = log_levels[log_level]
    except:
        logging.info(f"{log_level} is not a valid log level value")
        selected_log_level = logging.INFO
    finally:
        logging.getLogger().setLevel(selected_log_level)
        logging.info(
            f"log level set to {next(k for (k, v) in log_levels.items() if v == selected_log_level)}"
        )


def main():
    logging.info("config from environment:")
    for k in ["LOG_LEVEL", "BACKEND_URL"]:
        logging.info(f"    {k}: {os.environ.get(k)}")
    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

    # worker configuration
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    job_check_interval = float(os.environ.get("JOB_CHECK_INTERVAL", 10))

    client = Client(url=backend_url)
    worker = Worker(client=client, job_check_interval=job_check_interval)
    worker.work()


if __name__ == "__main__":
    main()
