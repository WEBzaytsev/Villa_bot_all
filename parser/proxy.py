import json
import random
from os import environ
from time import time
from typing import List, Literal

import requests

from settings import PROXY


class Proxy():
    def __init__(self, ip) -> None:
        self.ip: str = ip
        self.status: Literal["unchecked",
                             "ratelimited", "ok", "dead"] = "unchecked"
        self.last_used: int = None

    def __repr__(self) -> str:
        return self.ip

    def __str__(self) -> str:
        return self.ip


class Rotator:
    """weighted random proxy rotator"""

    def __init__(self, proxies: List[Proxy]):
        self.proxies = proxies

    def weigh_proxy(self, proxy: Proxy):
        weight = 1000
        if proxy.last_used:
            _seconds_since_last_use = time() - proxy.last_used
            if proxy.status == "dead":
                weight -= 900
            if proxy.status == "ratelimited" and _seconds_since_last_use < 86400:
                weight -= 1000
            if proxy.status == "ratelimited" and _seconds_since_last_use > 86400:
                weight += 150
            else:
                weight += _seconds_since_last_use
        if proxy.status == "unchecked":
            weight += 250

        return weight

    def get(self):
        proxy_weights = [self.weigh_proxy(p) for p in self.proxies if p.status in [
            "unchecked", "ok"] or (p.status == "ratelimited" and (time() - p.last_used) > 86400)]
        self_proxies = [p for p in self.proxies if p.status in ["unchecked", "ok"] or (
            p.status == "ratelimited" and (time() - p.last_used) > 86400)]
        if self_proxies:
            proxy = random.choices(
                self_proxies,
                weights=proxy_weights,
                k=1,
            )[0]
            proxy.last_used = time()
            return proxy
        else:
            return None


proxies = [Proxy(p) for p in PROXY]
