import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:5000/view_staff")
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8')[:500])
except Exception as e:
    print(e)
