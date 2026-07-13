# TLS certificates

Nginx expects the following files in this directory:

- `fullchain.pem` — server certificate (with chain)
- `privkey.pem`   — private key

For internal use you can generate a self-signed cert:

```bash
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout privkey.pem -out fullchain.pem \
  -days 365 -subj "/CN=skills.internal"
```

For production, use your company CA or a real certificate.
