from keystoneclient.v2_0 import client as kc

old_token = 'MIID0wYJKoZIhvcNAQcCoIIDxDCCA8ACAQExDTALBglghkgBZQMEAgEwggIhBgkqhkiG9w0BBwGgggISBIICDnsiYWNjZXNzIjogeyJ0b2tlbiI6IHsiaXNzdWVkX2F0IjogIjIwMTUtMTEtMjhUMDc6NTY6MzAuNzgxMzM5IiwgImV4cGlyZXMiOiAiMjAxNS0xMS0yOVQwNzo1NjozMFoiLCAiaWQiOiAicGxhY2Vob2xkZXIiLCAidGVuYW50IjogeyJlbmFibGVkIjogdHJ1ZSwgImRlc2NyaXB0aW9uIjogIiIsICJuYW1lIjogInNlcnZpY2UiLCAiaWQiOiAiYjA0YmI3N2IzNGE4NGU0NDk5NzE4ZTgxYTMxYWY2NDYifSwgImF1ZGl0X2lkcyI6IFsiOUVZWk9jbHFSM3lDTENQemdTdnpQQSIsICJXWUl5V3VvaFJQRy1vWUhGek5xMzFBIl19LCAidXNlciI6IHsidXNlcm5hbWUiOiAibmV1dHJvbiIsICJyb2xlc19saW5rcyI6IFtdLCAiaWQiOiAiOWYzMGE4NTg3ZDc2NDMyODkxNTViY2I3OThjYTU3Y2IiLCAicm9sZXMiOiBbeyJuYW1lIjogImludGVybmFsX2FkbWluIn1dLCAibmFtZSI6ICJuZXV0cm9uIn0sICJtZXRhZGF0YSI6IHsiaXNfYWRtaW4iOiAwLCAicm9sZXMiOiBbIjRiNDcyNGUyYzRhZjQyOGQ4NGExM2E0MTc0YjI4NDk4Il19fX0xggGFMIIBgQIBATBcMFcxCzAJBgNVBAYTAlVTMQ4wDAYDVQQIDAVVbnNldDEOMAwGA1UEBwwFVW5zZXQxDjAMBgNVBAoMBVVuc2V0MRgwFgYDVQQDDA93d3cuZXhhbXBsZS5jb20CAQEwCwYJYIZIAWUDBAIBMA0GCSqGSIb3DQEBAQUABIIBADFYlrhQSRY-fziZxKDtH8i42O1xiTinHf8eqq87Mt-oj-yk7yXYJZkwO714qp30QqUc6M5o+WaVkL3D5tRjQzAbYXaWDO1JNZcU60qPfPBdoI2wgr5DSq0AEiGFvq7cEO5kYjXUlve08bsqzL5uswoCywVi4QzFJeKCDI7DJqq1tJsn+WgqUKwxbIUlKEqtnboHI-3Lsn-zfWMjq8tYPxoZxM7Tt03B8coYqS6vBBv9FknMuQoiSLNU9hPWJ0Sjvxh0Al1CyGE800y2P11wDfjHGFbEOb6xcwqYX1RT-a8xmjypskNNYo--3LXmgXJ3fHSu279yrDzhcYR-R-mDHtg='
old_token = 'MIIDtgYJKoZIhvcNAQcCoIIDpzCCA6MCAQExDTALBglghkgBZQMEAgEwggIEBgkqhkiG9w0BBwGgggH1BIIB8XsiYWNjZXNzIjogeyJ0b2tlbiI6IHsiaXNzdWVkX2F0IjogIjIwMTUtMTItMDdUMDk6MTA6NDMuMTY2NjQ5IiwgImV4cGlyZXMiOiAiMjAxNS0xMi0wN1QwOToyMDo0M1oiLCAiaWQiOiAicGxhY2Vob2xkZXIiLCAidGVuYW50IjogeyJlbmFibGVkIjogdHJ1ZSwgImRlc2NyaXB0aW9uIjogIiIsICJuYW1lIjogImFkbWluIiwgImlkIjogIjQ2MDhmZGJmNmI5NzQwOTdiZGE5ODMxNWNhYmJjNDljIn0sICJhdWRpdF9pZHMiOiBbIjU0Ri1YR3lvU1llallHMTQ1czcwLVEiXX0sICJ1c2VyIjogeyJ1c2VybmFtZSI6ICJjbG91ZF9hZG1pbiIsICJyb2xlc19saW5rcyI6IFtdLCAiaWQiOiAiMTM3OTUyYjExZTNkNDBkYmI4Y2NiNjE4MWE0NWI5MmEiLCAicm9sZXMiOiBbeyJuYW1lIjogImFkbWluIn1dLCAibmFtZSI6ICJjbG91ZF9hZG1pbiJ9LCAibWV0YWRhdGEiOiB7ImlzX2FkbWluIjogMCwgInJvbGVzIjogWyI2ZmJlYmRlNzQ5MjE0Y2NkYjUxZWIwODA0MjE1YjlmNiJdfX19MYIBhTCCAYECAQEwXDBXMQswCQYDVQQGEwJVUzEOMAwGA1UECAwFVW5zZXQxDjAMBgNVBAcMBVVuc2V0MQ4wDAYDVQQKDAVVbnNldDEYMBYGA1UEAwwPd3d3LmV4YW1wbGUuY29tAgEBMAsGCWCGSAFlAwQCATANBgkqhkiG9w0BAQEFAASCAQCPt4Mdq-AZQUH0hZgQlvXWCdoNVMSQMcP4vd6mR+nWflAVdusltKE6HYVj9Z+mZdNQdD7SrzVse5ZC9O+iohacxj5oQNU5ythWWqjiXMwVTK2gu3H7SQ8B5cWr7XM46zCf-1zSax6myf9raTmxQYDcD5Q3CqtGuVWFc69N0TDIicoDh+7M7S9zlj7OSinOhnUmkVHO0SILCpI8-4o3H-vBq+ub+Sm4FTCJjy0K7WxFWQqM+v0d9J2xfq+pV8f38sdZZkc4wiuaSbRrdj0kk7wM0S2-OtcZDJHdjXrllZUpt6HmGcBrLlKZmtR1zexwi8r9-adSkKTDNkuh56VgROwz'

kwargs = {
                                'username': 'cloud_admin',
                                'password': 'FusionSphere123',
                                'auth_url': 'https://identity.cascading.hybrid.huawei.com:443/identity-admin/v2.0',
                                #'token': old_token, 
                                'insecure': True,
                                'tenant_name': 'admin'
                            }
"""
g_admin_plain_password = None
def get_plain_password():
    global g_admin_plain_password
    if g_admin_plain_password:
        return g_admin_plain_password
    password = "N8296FGj0gDK1OA8djBQ50u/7CZvJ+RfE2qNhiGICE8="
    try:
        from FSComponentUtil import crypt
        g_admin_plain_password = crypt.decrypt(password)
    except Exception:
        pass
    return g_admin_plain_password  
 
print(get_plain_password())
import pdb;pdb.set_trace()
body = '{"tenant_id": "alsdkadsjlfkajwe"}}'
s = "tenant_id"
for q in "\"'":
    idx = body.lower().find("%s%s%s:" % (q, s.lower(), q))
    if idx > 0:
        break
old_project_str = body[idx: body.find(',', idx+1)]
old_project_id = old_project_str.split()[1].strip("\"'}")
print(old_project_id)

body = bytes(body.replace(old_project_id, new_project_id))                 
"""
keystoneclient = kc.Client(**kwargs)
token_info = keystoneclient.tokens._get(kwargs['auth_url'] + "/tokens/%s" % old_token, 'access')
import pdb;pdb.set_trace()
print token_info
