import ssl
import time
from pathlib import Path
import re

import urllib3
import websocket
from requests import Request, Session
from websocket import WebSocketApp

urllib3.disable_warnings()

HTTP_IP = '192.168.102.4'
HTTP_PORT = 8888

proxies = {
    'http': f'http://{HTTP_IP}:{HTTP_PORT}',
    'https': f'http://{HTTP_IP}:{HTTP_PORT}',
}


class Key():
    def __init__(self):
        self.esc = b'\x1b\x1b'
        # vt sequences
        self.home = b'\x1b[1~'
        self.insert = b'\x1b[2~'
        self.delete = b'\x1b[3~'
        self.end = b'\x1b[4~'
        self.pg_up = b'\x1b[5~'
        self.pg_down = b'\x1b[6~'
        self.f0 = b'\x1b[10~'
        self.f1 = b'\x1b[11~'
        self.f2 = b'\x1b[12~'
        self.f3 = b'\x1b[13~'
        self.f4 = b'\x1b[14~'
        self.f5 = b'\x1b[15~'
        self.f6 = b'\x1b[17~'
        self.f7 = b'\x1b[18~'
        self.f8 = b'\x1b[19~'
        self.f9 = b'\x1b[20~'
        self.f10 = b'\x1b[21~'
        self.f11 = b'\x1b[23~'
        self.f12 = b'\x1b[24~'
        # xterm sequences
        self.up = b'\x1b[A'
        self.down = b'\x1b[B'
        self.right = b'\x1b[C'
        self.left = b'\x1b[D'
        self.enter = b'\n'


class OpenBmcBase():
    def __init__(self, host=None, username='Administrator', password='superuser'):
        self.proxy = False
        self.username = username
        self.password = password
        self.host = host
        self.session = None
        self.init_session()

    def init_session(self):
        self.session = Session()
        self.session.verify = False
        post_data = {
            'data': [self.username, self.password],
        }
        self.post('/login', post_data)
        if self.token:
            self.session.headers.update({'X-XSRF-TOKEN': self.token})

    def __del__(self):
        if hasattr(self, 'session') and self.session:
            try:
                self.logout()
            except Exception:
                pass

    def send_request(self, prepped=None):
        if self.proxy:
            return self.session.send(prepped, proxies=proxies)
        return self.session.send(prepped)

    def get(self, url):
        url = f'https://{self.host}{url}'
        req = Request('GET', url)
        prepped = self.session.prepare_request(req)
        return self.send_request(prepped)

    def post(self, url, data):
        url = f'https://{self.host}{url}'
        req = Request('POST', url, json=data)
        prepped = self.session.prepare_request(req)
        return self.send_request(prepped)

    def patch(self, url, data):
        url = f'https://{self.host}{url}'
        req = Request('PATCH', url, json=data)
        prepped = self.session.prepare_request(req)
        return self.send_request(prepped)

    def delete(self, url):
        url = f'https://{self.host}{url}'
        req = Request('DELETE', url)
        prepped = self.session.prepare_request(req)
        return self.send_request(prepped)

    def logout(self):
        post_data = {
            'data': [],
        }
        resp = self.post('/logout', post_data)
        self.session = None
        return resp

    def force_restart(self):
        post_data = {
            'ResetType': 'ForceRestart'
        }
        self.post('/redfish/v1/Systems/system/Actions/ComputerSystem.Reset', post_data)

    @property
    def cookies(self):
        return '; '.join([str(x) + '=' + str(y) for x, y in self.session.cookies.items()])

    @property
    def token(self):
        try:
            return self.session.cookies.get('XSRF-TOKEN', None)
        except Exception:
            return None


class OpenBmcUtil(OpenBmcBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.key = Key()

    def websocket_sol_1(self):
        wsapp = WebSocketApp(f'wss://{self.host}/console0', on_message=self.on_message, cookie=self.cookies)
        if self.proxy:
            run_forever_opts = {
                'sslopt': {
                    'cert_reqs': ssl.CERT_NONE,
                    'check_hostname': False,
                },
                'http_proxy_port': str(HTTP_PORT),
                'http_proxy_host': HTTP_IP,
                'proxy_type': 'http',
            }
        else:
            run_forever_opts = {
                'sslopt': {
                    'cert_reqs': ssl.CERT_NONE,
                    'check_hostname': False,
                },
            }
        wsapp.run_forever(**run_forever_opts)

    def on_message(self, wsapp, message):
        print(f'message: {message}')
        sol = Path('sol.log')
        with sol.open('ab') as fd:
            fd.write(message)

    def websocket_sol_2(self):
        ssl_opts = {
            'cert_reqs': ssl.CERT_NONE,
            'check_hostname': False,
        }
        if self.proxy:
            all_opts = {
                'sslopt': ssl_opts,
                'http_proxy_port': str(HTTP_PORT),
                'http_proxy_host': HTTP_IP,
                'proxy_type': 'http',
                'cookie': self.cookies,
                'subprotocols': [self.token],
            }
        else:
            all_opts = {
                'sslopt': ssl_opts,
                'cookie': self.cookies,
                'subprotocols': [self.token],
            }
        ws = websocket.create_connection(f'wss://{self.host}/console0', **all_opts)
        print('Restart SUT')
        self.force_restart()
        end_time = time.time() + 180
        buffer = b''
        print('Wait for keyword: "Entering Setup...')
        while time.time() < end_time:
            try:
                msg = ws.recv()
                if msg:
                    buffer += msg
                if b'Entering Setup...' not in buffer:
                    ws.send(self.key.delete)
                else:
                    ws.send(self.key.right)
                    time.sleep(0.5)
                    ws.send(self.key.down)
                    time.sleep(0.5)
            except Exception:
                pass
        ws.close()


def main():
    obmc_opts = {
        'host': '192.168.159.252',
        'username': 'Administrator',
        'password': 'superuser',
    }
    obmc = OpenBmcUtil(**obmc_opts)
    obmc.websocket_sol_2()


if __name__ == '__main__':
    main()
