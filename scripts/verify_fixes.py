import urllib.request

req = urllib.request.urlopen('http://127.0.0.1:8000/')
html = req.read().decode('utf-8')

assert 'id="navbar-audio-toggle"' in html, 'Navbar audio toggle missing!'
assert 'btn-hero-audio' not in html, 'Duplicate hero audio button still present!'
assert 'id="pain-slider"' in html, 'Pain slider missing!'
assert 'class="pain-range-slider"' in html, 'Pain range slider class missing!'
assert 'pain-num-btn' not in html, 'Old pain buttons still present!'

print("SUCCESS: Single mute button and sliding severity bar confirmed on live server!")
