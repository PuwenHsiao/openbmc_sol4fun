import ssl
from pathlib import Path

import urllib3
from requests import Request, Session
from websocket import WebSocketApp

urllib3.disable_warnings()

HTTP_IP = '192.168.160.65'
HTTP_PORT = 8888

proxies = {
    'http': f'http://{HTTP_IP}:{HTTP_PORT}',
    'https': f'http://{HTTP_IP}:{HTTP_PORT}',
}


class OpenBmcBase():
    def __init__(self, host=None, username='Administrator', password='superuser'):
        self.proxy = True
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


def main():
    obmc_opts = {
        'host': '192.168.159.252',
        'username': 'Administrator',
        'password': 'superuser',
    }
    obmc = OpenBmcUtil(**obmc_opts)
    obmc.websocket_sol_1()


if __name__ == '__main__':
    main()
