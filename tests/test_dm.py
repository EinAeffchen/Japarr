import pytest
from japarr.adapters.discord import DiscordConnector
from japarr.adapters.jraws import JRawsDownloader
from parsel import Selector


def test_get_article_quality():
    jr = JRawsDownloader("discord")
    text = "<code>WEB-DL 1080p | HD: 3.8GB (approx.) | NG</code>"
    output = jr._get_article_quality(text)
    assert output[0] == "WEB-DL 1080p"
    assert output[1] == "HD: 3.8GB (approx.)"
    assert output[2] == "NG"


def test_parse_download():
    html = """
    <div id="download-list"><div style="margin-bottom:10px">
        <code>WEB-DL 720p, 480p | HD: 1.0GB / SD: 0.5GB (approx.) | NG</code>
        </div><div style="margin-top:20px"><div class="ren-res">720p</div>
        <a href="/download/?hash=RGlXVVFGMktWalZOL0h3RTk5VlRrODNnWWRqdEZkT2pBb3Vwc28yOHhoYnZNT3pIUm5STXNIeHJOSXBnZjlZTE5hWEZISm51a0JWT0Jpa2hHTGR6MUJ1MGNtY0U0NEllV0lURmg2aGFadGNpRG1BeVVmM291aTU1dE13LzcxSS9aNkN2ZDlCNzJLWnlqd21rTkFMZnhnPT0mJmI3ODg3ODAxY2Q0N2UzNDg2N2YxYTM1ZWZmM2M0MjUy&id=726&ep=1">
        <span class="episode">1</span></a>
        <a href="/download/?hash=RmlrSnZvaHdsbGVlOHdoS25qNWl4ejBaSTgzWnZZTXZVOGYxaHE1RE1PaEZZaUphSmNXeTNRQ0RBQXlDaXdsODRyL0lyVXZXcm52S1FGNGs0SFVCcWl2emtVaDM0b0xhY2h2dHo3VUc3dWNXUEVQUDhxZGdVY3hQUnUrYy9HWGw3SU5wNDBrdSszQ0VsQ0g1VXlDdjBnPT0mJjhmMjY2Y2QzYjdmMmNiMjg1YTMyN2U1ZGMxYmIzYjAx&id=726&ep=2">
        <span class="episode">2</span></a>
        <a href="/download/?hash=WklLdFB4VDdvSlJlTWdsSXNiby9jQVhJbGRSZDVBOXRQVVR5UHM2OGVWa1F0MkdqdXZGczJLV1RmNmhHdG9yMFhQMklmbkdvYUloUktoVStZMDEyWFFVMWFpKzlvbkw1Y0p0bXN0Wll4dzdrNldvcmVaZDdPOGs5RHVmQUVDbDN0Z1creFlzSVAzekRuVTVqM2lMcHRRPT0mJmJhOTcxMzllNTEzY2MzOTQ3ZTAzMjhhMWI0Njk1NTFk&id=726&ep=3">
        <span class="episode">3</span></a>
        <a href="/download/?hash=TVRIeVBUakhIVURIV1lCMkFtVkdydi9xSkhiZjFJRFFTNkwvUE1BTkVVOXdOelhaSzY5Y21kd3FHdHZmUlEzaWZsQ0I4Z3A4WVFUOFZyYnpHVFZubEY1RHdZVGltMjFTc0FRdElJRzdreXQvYWRpUlhoeEZ2SVIzYkZ6T0w3UTVsY21mL2E4L3Qyd05JT0VBZlRtTkZBPT0mJmY2YTBhYjUyZTY3YTFiMTg1NDdiZjgwYmY5YzliNDRk&id=726&ep=4">
        <span class="episode">4</span></a>
        <a href="/download/?hash=dEVlUW45VHlzWEVhaUFBdEN0TElIMU45dURzdmo4UTZDQ01RZHlEQXZKdnU5VFROZTlsa3RXUkpMZXZKaGNtVjVCMWsyb01ReEhXTWx1WkYvTk1wMHVKMnI0bkFMK1BMVklLR3c3enBZNi9Maml4bXAvMjBWQk83cnVrU254aUJQQTdQclRzR05ERWhTaThEQmJTTFVBPT0mJjRiNzExOWJmMzA0NDkzNjdlNWQyZjMxMjRiMTMyMGVi&id=726&ep=5">
        <span class="episode">5</span></a>
        <a href="/download/?hash=UFp5Ykx2aElKZ3F6RkNnbmxIM1VtRjNGK3J1RTV3L3F6OW1NN0F5ZGJTMEZmQTZuNXJPRXpsb0ZpamFTc0UrVUkyZ21HaWIwQWdLYVNpOHRrNEZvOG9KTWdjdmNJTXJaRENmRURXTXRZRDRQa1prK3JtanFpVG84ZUU2eGdYSFZrUUlQWlNqczhqamk2Mmo2bmdaUm93PT0mJmEwMDU4ZmE0MTY2ZDJiYTM2MDFiZDc2MWQxOWY5ZjQ1&id=726&ep=6">
        <span class="episode">6</span></a>
        <a href="/download/?hash=ODYrK0pkZzMyWGNmR1Y1dFlpQ2loMFp3aVBaeWtOWjVkZnNQVVFub2w4YmVXcUZOVE5DK3g5dVc4Zk80dS9DZzFwRWN0dm1neVR2czhLU3MzQW12b0s4SmFTK0U0Uit2bDhlZi8xK2E4UGo0RmFCMTkvbzlNRnkrODU5UXVCeklLN3haMkhsZnBZNjhPcHBJL201QndBPT0mJjAyMTJlNTk5NDQyNTRjZWQ2NGQ2ZjA1YWM3YzJmMjA0&id=726&ep=7">
        <span class="episode">7</span></a>
        <a href="/download/?hash=SEpQVXI5WFB6R2F2WnU4WGJ4T1FUYmJ0MzBmREFyNVVjNlV3bElSS0NpdjNramE4Q0dVdE5QU0xFbXZwNnphTjVxalBwN1U0bXNORjZ5RUtPNWxIR0lpSHd3VnlpRDI0cDc2U1YrREZOZHpSV0xvNFRCU1hiRU9lN04zTEZ6bWh2UWFRYjQvK24vZWNtK01KbStzRHVBPT0mJjEwOGQ1MDY2N2NiMzYwOWNmZGI0ZjA4MTI5N2E5NTVm&id=726&ep=8">
        <span class="episode">8</span></a>
        <a href="/download/?hash=dXpmTDdqRU1QbTdMUm5EUnlrbzg1WWFnc1prU3pFdFJLcFU2cTZ0RUQ0ZEo1cis3bFo0cUxTM1ZvSWYrVks4QVFFUU4xWUFoWXl1Q1N2YStIaldURVU2dzNuK1U1OXExbm5ERThTOEt0WFcyc09ucGpONWZvTUxudXNhZUhBRkVKMUZJdkx0TVlzMVFYRzhQSlEzOWZBPT0mJmRjMzRlMTBmOWJlMWE3NjRjZmFiZGY5NTE1NWEyZmI3&id=726&ep=9">
        <span class="episode">9</span></a>
        <a href="/download/?hash=U05xK29kVW5EL0hBTkRvRjE0VnkzWXJXajBrbFc3U2pRRk9rdkU4VXdTaDdkWk1Za2cwOTZrazY4NXJkT3hMdU9Gb29ZWFhYQUNJak51WHo5Uk5qTFJYaXE1RVovZ29BRklnQm1CaXkwTnh4ZlIzSE51WEEyc0VreDI4SGtZKzBuVWkzVGc2bC9lMGJhTTZ4VGpKZjd3PT0mJjY1Mzg1ZmQyOWNhZWFlZmNhY2FmYjMxZDg0ODllZjAw&id=726&ep=10">
        <span class="episode">10</span></a>
    </div>"""
    sel = Selector(html)
    jr = JRawsDownloader("discord")
    downloads = jr._parse_download(sel)
    assert len(downloads) == 10
