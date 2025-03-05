import atexit
from http import HTTPStatus
from threading import Thread
from uuid import uuid4

from flask import Flask, make_response
from flask_apscheduler import APScheduler

from eventfully.config import CONFIG
from eventfully.database import crud
from eventfully.logger import log
from eventfully.routes import account, api, index, legal_notice
from eventfully.search import post_processing, crawl

log.info("Starting Server v0.4.0 ...")
crud.create_tables()

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False


# Cron Background tasks mainly for searching for events
scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())

scheduler.add_job("collect", crawl.main, trigger="cron", day="*", max_instances=1)

scheduler.start()

# Background Tasks that run continuously
post_process_thread = Thread(target=post_processing.main)
post_process_thread.start()


@app.errorhandler(500)
def internal_error_server_error(error):
    """
    When something goes wrong on the server side, this error is returned.
    """

    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


app.register_blueprint(api.bp)
app.register_blueprint(index.bp)

if CONFIG.EVENTFULLY_LEGAL_NOTICE:
    app.register_blueprint(legal_notice.bp)

if CONFIG.EVENTFULLY_ACCOUNTS_ENABLED:
    app.register_blueprint(account.bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CONFIG.EVENTFULLY_PORT, debug=True)
