from japarr.adapters.jraws import JRawsDownloader
from parsel import Selector

from japarr.media_objects import Movie


def test_get_article_quality():
    jr = JRawsDownloader("discord")
    text = "WEB-DL 1080p | HD: 3.8GB (approx.) | NG"
    output = jr._get_article_quality(text)
    assert output[0] == "WEB-DL 1080p"
    assert output[1] == "HD: 3.8GB (approx.)"
    assert output[2] == "NG"


def test_parse_download():
    html = """
    <div style="margin-top:20px">
        <div class="ren-res">1080p</div>
        <a href="/download/?hash=RmhnZ2NsZ0tVTThyNVNHdTI2emFodFI2aVI0ZzZxRFR0Z0ZNZjZRZndCVmJHbDQyeVdaSE1yNXpHTVpBNnZWZWlpUVpTeVplcGc0NnI4SGIyOGk0NXphSXg4bityZHU4TEJ0bHFsQTkzNExMOWx5YUNuUjZMRkN4VE90a28rYkwwamlVWk0weCt2L3UwcXkzTXhKV3hBPT0mJmE0YzI3OWUxNDI1MDQxYzM0MWI4ZmQ4NTFkODgyNDdm&amp;id=1449&amp;ep=1">
        <span class="episode">1</span></a><a href="/download/?hash=YlVFK282U3NTOWU0SVRUcm53S0FxNVVsY1RGSTZpNExPOFlSZ20zTjFRSm5qb2h6Z3gvYXZXeXpDOWNDV2JUbDc5a2tzS3o4UFAwNmY3K0pvdXJTYW1hcjY2RzZQVTVDaktGQzZwdEVubkVGRGVuYU56NkZhNkVYREF6UXdOZ2F4TEJYWXh0YjVBbjErZW9YMzJXVzVRPT0mJjE2NjZmMjYzMTVmNDk1OTA0NGQ5NzNkYTBhYzExNmJj&amp;id=1449&amp;ep=2">
        <span class="episode">2</span></a><a href="/download/?hash=dVMvc2dDVE8yUTJybEtnV0ExQm1SaFA3dyt0RXY2eHFSeE52aGU3ODBFZ2ZpVUVDUS9rcEZqc05XWmcxTTUySWZtYXZCVXgyc1ptSXJpME9tUGx6TXNQRjZvNUlBdDFCai9lYWtPaFBGekFJYTFLc25sK0ttS0YraE5tMjVBNXRqMWFmR0JBbFFmZTh0ZG5tVjNtWEd3PT0mJmNjZjM5MmJmODc2M2IwODliOTBiYzJhZGZmY2I5OWZh&amp;id=1449&amp;ep=3">
        <span class="episode">3</span></a>
    </div>
    """
    sel = Selector(html)
    jr = JRawsDownloader("discord")
    downloads = jr._parse_download(sel.xpath("//body/div"))
    assert len(downloads) == 3


def test_parse_media_details():
    url = "https://jraws.com/drama/1351341039/"
    jr = JRawsDownloader("discord")
    media_dict = jr.parse_media_details(url)
    assert media_dict["jap_title"] == "ドライフラワー －七月の部屋－"
    assert media_dict["quality"] == "WEB-DL 1080p"
    assert len(media_dict["download_urls"]) == len(
        {
            1: "https://jraws.com/download/?hash=c3hoRUxrQkY2REJNUHZyVVh3eTgwVzR5SXpEMXY1NjZVZVZsSkhyb2Q2UnpGUlV0Ukl2UmhSejYwNE1sWEh6NGhMUEltQVloR2g0cVlVOFRyQS9RVWdwZUtWZVBhaU5xUmladWV5SEtFUmRnQlZWbHNic1c1YnVLYXlncTRIMHA4cGdsU0ZUMEYrbEdRazN4MzZWNE9nPT0mJjczNjNkMzRhOThmZTVhOThmOTIyN2E5OWZhNTA4ZjEy&amp;id=1449&amp;ep=1",
            2: "https://jraws.com/download/?hash=UkRhNGpZWlJKa0MvTXg0VnNKZlE1d0J6Q2tueTFad0I4eGRZamdEZ09IL1d5ZEVMWmZHU25BeWIxWXYwZm5wcHYwZ3JYNVBsNHFqZVNhaFkvYkJFaFpNSWxSSW5MSDdrcGZhVDFYemJvNFdJRW80b0pTQmFOY3NEWW1QQU83NFpxZWtMaUs4K3dzbUQxUlc3cjh6eGpnPT0mJmMxOTUxOTQxZDQzZGIwMTM4MmU4ZTYzNjQyMTY5NzFj&amp;id=1449&amp;ep=2",
            3: "https://jraws.com/download/?hash=ejIwUEFrbkxPdVpYMTFmS1huT3h1bWY0NHNrNUVTUUVCZEo2U2dEa3d0eTBUYVVOQ083aWtGUnVNcnVlZUxDNThkMzVSY29DRlI5WmlpZFA1RXJTNDFXbEVaSURBZmNGTUJWTWhKVXVCT096Z05SbzRJLzZxQ2VqMlZYMklPVUVxamVaUG9XdTlJclFQTjlGR09wUXNBPT0mJjc1Y2M0ZTlhNzQwMWU0MzcxZTU2ZWQyMGYzNWQxMTYx&amp;id=1449&amp;ep=3",
        },
    )


def test_create_media_obj():
    jr = JRawsDownloader("discord")
    media_obj = jr._create_media_obj(
        "movie",
        None,
        "Test movie",
        "http://somewhere.com",
        "Still a test movie",
    )
    assert isinstance(media_obj, Movie)
    assert media_obj.english_title == "Still a test movie"
    assert media_obj.title == "Test movie"
    assert media_obj.url == "http://somewhere.com"
