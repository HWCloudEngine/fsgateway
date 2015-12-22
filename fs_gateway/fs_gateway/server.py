import sys

from fs_gateway import config
from fs_gateway.common import log as logging
from fs_gateway import service

def main(servername):
    config.parse_args(sys.argv)
    logging.setup("fs_gateway")
     

    launcher = service.process_launcher()
    server = service.WSGIService(servername, use_ssl=False,
                                         max_url_len=16384)
    launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()
    
