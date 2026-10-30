from app.common.storage.file_types import JPEG, PDF, PLAIN_TEXT, PNG, WEBP, extension_of


def test_signatures_recognize_real_files_only():
    assert PNG.fits(b"\x89PNG\r\n\x1a\n....")
    assert JPEG.fits(b"\xff\xd8\xff\xe0")
    assert WEBP.fits(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    assert PDF.fits(b"\n%PDF-1.7")
    assert not PNG.fits(b"MZ\x90\x00")
    assert not PDF.fits(b"<html>")


def test_text_is_utf8_without_nul_bytes():
    assert PLAIN_TEXT.fits("Xin chào".encode())
    # A sample cut inside a multi-byte character is still text.
    assert PLAIN_TEXT.fits("Xin chào".encode()[:-1])
    assert not PLAIN_TEXT.fits(b"abc\x00def")
    assert not PLAIN_TEXT.fits(b"\xff\xfe\xfa\xfb" * 4)


def test_extension_of():
    assert extension_of("Báo cáo.PDF") == ".pdf"
    assert extension_of(".bashrc") == ""
    assert extension_of("noext") == ""
