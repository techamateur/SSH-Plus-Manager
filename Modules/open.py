#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenVPN-style HTTP proxy for SSH Plus (default port 8080). Used by connections module."""
import socket
import threading
import select
import sys
import time
from os import system
system("clear")

IP = '0.0.0.0'
try:
    PORT = int(sys.argv[1])
except (IndexError, ValueError):
    PORT = 8080
PASS = ''
BUFLEN = 8196 * 8
TIMEOUT = 60
MSG = 'SSHPLUS'
DEFAULT_HOST = '0.0.0.0:1194'
RESPONSE = "HTTP/1.1 200 " + str(MSG) + "\r\n\r\n"

class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.running = False
        self.host = host
        self.port = port
        self.threads = []
	self.threadsLock = threading.Lock()
	self.logLock = threading.Lock()

    def run(self):
        self.soc = socket.socket(socket.AF_INET)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(2)
        self.soc.bind((self.host, self.port))
        self.soc.listen(0)
        self.running = True

        try:                    
            while self.running:
                try:
                    c, addr = self.soc.accept()
                    c.setblocking(1)
                except socket.timeout:
                    continue
                
                conn = ConnectionHandler(c, self, addr)
                conn.start()
                self.add_conn(conn)
        finally:
            self.running = False
            self.soc.close()
            
    def print_log(self, log):
        with self.log_lock:
            print(log)

    def add_conn(self, conn):
        try:
            self.threads_lock.acquire()
            if self.running:
                self.threads.append(conn)
        finally:
            self.threads_lock.release()

    def remove_conn(self, conn):
        try:
            self.threads_lock.acquire()
            self.threads.remove(conn)
        finally:
            self.threads_lock.release()

    def close(self):
        try:
            self.running = False
            self.threads_lock.acquire()
            threads = list(self.threads)
            for conn in threads:
                conn.close()
        finally:
            self.threads_lock.release()


class ConnectionHandler(threading.Thread):
    def __init__(self, socClient, server, addr):
        threading.Thread.__init__(self)
        self.clientClosed = False
        self.targetClosed = True
        self.client = socClient
        self.client_buffer = ''
        self.server = server
        self.log = 'Connection: ' + str(addr)

    def close(self):
        try:
            if not self.clientClosed:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
        except:
            pass
        finally:
            self.clientClosed = True
            
        try:
            if not self.targetClosed:
                self.target.shutdown(socket.SHUT_RDWR)
                self.target.close()
        except:
            pass
        finally:
            self.targetClosed = True

    def run(self):
        try:
            self.client_buffer = self.client.recv(BUFLEN)
        
            hostPort = self.findHeader(self.client_buffer, 'X-Real-Host')
            if host_port == '':
                host_port = DEFAULT_HOST
            split = self._find_header(self.client_buffer, 'X-Split')
            if split != '':
                self.client.recv(BUFLEN)
            if host_port != '':
                passwd = self._find_header(self.client_buffer, 'X-Pass')
                if PASS and passwd == PASS:
                    self._method_connect(host_port)
                elif PASS and passwd != PASS:
                    self.client.send(b'HTTP/1.1 400 WrongPass!\r\n\r\n')
                elif host_port.startswith(IP):
                    self._method_connect(host_port)
                else:
                    self.client.send(b'HTTP/1.1 403 Forbidden!\r\n\r\n')
            else:
                print('- No X-Real-Host!')
                self.client.send(b'HTTP/1.1 400 NoXRealHost!\r\n\r\n')

        except Exception as e:
            self.log += ' - error: ' + getattr(e, 'strerror', str(e))
            self.server.print_log(self.log)
        finally:
            self.close()
            self.server.remove_conn(self)

    def _find_header(self, head, header):
        """Extract HTTP header value; head must be str."""
        idx = head.find(header + ': ')
        if idx == -1:
            return ''
        idx = head.find(':', idx)
        head = head[idx + 2:]
        idx = head.find('\r\n')
        return head[:idx] if idx != -1 else ''

    def _connect_target(self, host_str):
        """Resolve host:port and connect; for CONNECT, default port 443."""
        i = host_str.find(':')
        if i != -1:
            port = int(host_str[i + 1:])
            host_str = host_str[:i]
        else:
            port = 443
        family, typ, proto, _, address = socket.getaddrinfo(host_str, port)[0]
        self.target = socket.socket(family, typ, proto)
        self.targetClosed = False
        self.target.connect(address)

    def _method_connect(self, path):
        self.log += ' - CONNECT ' + path
        self._connect_target(path)
        self.client.sendall(RESPONSE)
        self.client_buffer = ''
        self.server.print_log(self.log)
        self._do_connect()

    def _do_connect(self):
        """Bidirectional relay between client and target."""
        socs = [self.client, self.target]
        count = 0
        error = False
        while True:
            count += 1
            r, _, err = select.select(socs, [], socs, 3)
            if err:
                error = True
            if r:
                for sock in r:
                    try:
                        data = sock.recv(BUFLEN)
                        if data:
                            if sock is self.target:
                                self.client.send(data)
                            else:
                                while data:
                                    sent = self.target.send(data)
                                    data = data[sent:]
                            count = 0
                        else:
                            break
                    except OSError:
                        error = True
                        break
            if count == TIMEOUT:
                error = True
            if error:
                break



def main():
    """Run proxy server; Ctrl+C to stop."""
    print("\033[0;34m━\033[0m" * 8 + " \033[1;32m PROXY SOCKS \033[0;34m━\033[0m" * 8 + "\n")
    print("\033[1;33mIP:\033[1;32m " + IP)
    print("\033[1;33mPORT:\033[1;32m " + str(PORT) + "\n")
    server = Server(IP, PORT)
    server.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping...")
        server.close()


if __name__ == '__main__':
    main()
