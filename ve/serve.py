"""Máy chủ tệp cục bộ cho media/ của dự án trong lúc render.

Bộ dựng được đóng gói một lần và dùng chung cho mọi dự án, nên file của dự án (video đã cắt, logo, ảnh sản phẩm)
được phục vụ qua http://127.0.0.1:<cổng>/ thay vì chép vào gói (tránh chép hàng trăm MB mỗi lần).
"""
from __future__ import annotations

import contextlib
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):  # im lặng
        pass


@contextlib.contextmanager
def media_server(root: Path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Handler, directory=str(root)))
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()
        srv.server_close()
