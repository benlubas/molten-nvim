import json
import time
import uuid
from queue import Empty as EmptyQueueException
from queue import Queue
from threading import Thread
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from molten.runtime_state import RuntimeState


class JupyterAPIClient:
    def __init__(self,
                 url: str,
                 kernel_info: Dict[str, Any],
                 headers: Dict[str, str]):
        self._base_url = url
        self._kernel_info = kernel_info
        self._headers = headers

        self._recv_queue: Queue[Dict[str, Any]] = Queue()

        import requests
        self.requests = requests

    def get_stdin_msg(self, **kwargs):
        return None

    def wait_for_ready(self, timeout: float = 0.):
        start = time.time()
        while True:
            response = self.requests.get(self._kernel_api_base,
                                    headers=self._headers)
            response = json.loads(response.text)

            if response["execution_state"] != "idle" and time.time() - start > timeout:
                raise RuntimeError

            # Discard unnecessary messages.
            while True:
                try:
                    response = self.get_iopub_msg()
                except EmptyQueueException:
                    return


    def start_channels(self) -> None:
        import websocket

        parsed_url = urlparse(self._base_url)
        self._socket = websocket.create_connection(f"ws://{parsed_url.hostname}:{parsed_url.port}"
                                                   f"/api/kernels/{self._kernel_info['id']}/channels",
                                                   header=self._headers,
                                                   )
        self._kernel_api_base = f"{self._base_url}/api/kernels/{self._kernel_info['id']}"

        self._iopub_recv_thread = Thread(target=self._recv_message)
        self._iopub_recv_thread.start()

    def _recv_message(self) -> None:
        while True:
            response = json.loads(self._socket.recv())
            self._recv_queue.put(response)

    def get_iopub_msg(self, **kwargs):
        if self._recv_queue.empty():
            raise EmptyQueueException

        response = self._recv_queue.get()

        return response

    def execute(self, code: str):
        header = {
            'msg_type': 'execute_request',
            'msg_id': uuid.uuid1().hex,
            'session': uuid.uuid1().hex
        }

        message = json.dumps({
            'header': header,
            'parent_header': header,
            'metadata': {},
            'content': {
                'code': code,
                'silent': False
            }
        })
        self._socket.send(message)

    def shutdown(self):
        self.requests.delete(self._kernel_api_base,
                        headers=self._headers)

    def cleanup_connection_file(self):
        pass

class JupyterAPIManager:
    def __init__(self,
                 url: str,
                 ):
        parsed_url = urlparse(url)
        self._base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        token = parse_qs(parsed_url.query).get("token")
        if token:
            self._headers = {'Authorization': f'token {token[0]}'}
        else:
            # Run notebook with --NotebookApp.disable_check_xsrf="True".
            self._headers = {}

        import requests
        self.requests = requests

    def start_kernel(self) -> None:
        url = f"{self._base_url}/api/kernels"
        response = self.requests.post(url,
                                 headers=self._headers)
        self._kernel_info = json.loads(response.text)
        assert "id" in self._kernel_info, "Could not connect to Jupyter Server API. The URL specified may be incorrect."
        self._kernel_api_base = f"{url}/{self._kernel_info['id']}"

    def client(self) -> JupyterAPIClient:
        return JupyterAPIClient(url=self._base_url,
                                kernel_info=self._kernel_info,
                                headers=self._headers)

    def interrupt_kernel(self) -> None:
        self.requests.post(f"{self._kernel_api_base}/interrupt",
                      headers=self._headers)

    def restart_kernel(self) -> None:
        self.state = RuntimeState.STARTING
        self.requests.post(f"{self._kernel_api_base}/restart",
                      headers=self._headers)
