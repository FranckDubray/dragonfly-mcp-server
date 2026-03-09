import requests

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NzIwMDcwMTEsImV4cCI6MTc3MjYxMTgxMSwicm9sZXMiOlsiUk9MRV9VU0VSIiwiUk9MRV9BRE1JTiJdLCJ1c2VybmFtZSI6InRlc3RAY2FtaWxsZS5jb20ifQ.FJYOn5Sptn8ZvBOCV_QakDQP8PQMYYJMGzUC6qo_S2Lj6fsUC6dsNGKPzsylsVJYxu79hXSrLWGAERVcxbjz7wqGUYI8ChTPHo1hE8RJj_1IMk5GPLMiHFNSUXMLD6cHCl-_-D7WGD_Ryb-odBH-U7nSv2Mt6YedXFCKlCEhOgzwBznQ0wS4Jxgy2pTBudOXd24ICshr6G-kvZqiyoZci830Nq67-4Iy-rhulZeuwF9Sh9nB7yY38dmk5iYFIU2TLAvc0tUoz2JjGQRQq2LV9VugBJj2KQF9l0Fs_3rY16PtPp7AUgqrb3l4uiK502Xp_T_fMiAyE5_HKaecmiOvxg"

url = "http://localhost:8000/api/v1/s3/object?scope=user&path=file_not_exist.txt&json=true"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
resp = requests.get(url, headers=headers)
print(resp.status_code)
print(resp.text)
