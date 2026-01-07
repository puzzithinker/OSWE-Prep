# .NET ViewState Deserialization Case Study

## Environment
**Application**: DotNetNuke 9.1.1
**Framework**: ASP.NET 4.5
**IIS**: Windows Server 2016

## Vulnerable Code
```csharp
// web.config with hardcoded machine keys
<machineKey validationKey="ABC123..." decryptionKey="DEF456..." validation="SHA1" decryption="AES" />
```

## Chain Outline
1. Extract ViewState from page source
2. Decode and analyze ViewState structure
3. Locate machine keys in web.config
4. Generate malicious ViewState with ysoserial.net
5. Submit crafted ViewState
6. Achieve RCE via ObjectDataProvider

## Findings
**Root Cause**: Hardcoded machine keys + deserialization without validation
**Fix**: Remove machine keys from web.config, use ViewStateEncryptionMode=Always, update to .NET 4.8+
