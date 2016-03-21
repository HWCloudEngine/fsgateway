import sys

from fsgateway import config
from fsgateway.common import log as logging
from fsgateway import service

def main(servername):
    config.parse_args(sys.argv)
    logging.setup("fsgateway")
     

    launcher = service.process_launcher()
    server = service.WSGIService(servername, use_ssl=False,
                                         max_url_len=16384)
    launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()


def api():
    config.parse_args(sys.argv)
    logging.setup("fsgateway")

    launcher = service.process_launcher()
    server = service.WSGIService('rest', use_ssl=False, max_url_len=16384)
    launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()
    
def proxy():
    config.parse_args(sys.argv)
    logging.setup("fsgateway")

    launcher = service.process_launcher()
    server = service.WSGIService('proxy', use_ssl=False, max_url_len=16384)
    launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()

