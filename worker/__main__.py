import logging
import os

from client import Client

from worker import Worker


LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logging.info("config from environment:")
    for k in ["LOG_LEVEL", "BACKEND_URL"]:
        logging.info(f"    {k}: {os.environ.get(k)}")

    if os.environ.get("LOG_LEVEL", "INFO") in LOG_LEVELS.keys():
        log_level = LOG_LEVELS[os.environ.get("LOG_LEVEL", "INFO")]
    else:
        log_level = LOG_LEVELS["INFO"]

    logging.getLogger().setLevel(log_level)
    logging.info(f"log level set to {log_level}")

    # worker configuration
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    logging.info(f"backend url set to: {backend_url}")
    job_check_interval = float(os.environ.get("JOB_CHECK_INTERVAL", 10))

    client = Client(url=backend_url)
    worker = Worker(client=client, job_check_interval=job_check_interval)
    worker.work()


if __name__ == "__main__":
    main()
