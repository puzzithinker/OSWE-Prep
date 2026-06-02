# .NET ViewState Deserialization Case Study

## Environment

- Host OS: Windows Server (target), Kali (attacker)
- App: ASP.NET WebForms or older MVC apps, DotNetNuke < 9.1.1 (classic example), or any app using `__VIEWSTATE` with default or weak machine keys.
- Framework: .NET Framework 4.x (BinaryFormatter / ObjectStateFormatter are dangerous)
- IIS
- Web URL: http://target/
- Key ports: 80/443 (plus any management)

**Classic vulnerable target**: DotNetNuke 9.1.0 with known/hardcoded or discoverable machineKey in web.config.

## Recon

- Entry points: Any page that posts back `__VIEWSTATE` (most .NET WebForms pages have it in every form). Also `__VIEWSTATEENCRYPTED`, `__EVENTVALIDATION`.
- Roles: Often unauthenticated or low-priv pages can carry ViewState; deserial happens server-side on postback before auth checks in some cases.
- Sinks: `LosFormatter`, `ObjectStateFormatter`, `BinaryFormatter` (via ViewState deserial path), or JSON.NET with TypeNameHandling.

**Indicators**:
- Hidden field named `__VIEWSTATE` containing long base64 (sometimes starts with `/wE...` or similar).
- `web.config` or `machine.config` containing `<machineKey ...>` with `validationKey` / `decryptionKey`.
- Apps using `Page.ViewStateUserKey` not set or predictable.

## Vulnerability Hypothesis

- Suspected class: Insecure .NET deserialization via ViewState (or related formatter).
- Data flow: Attacker obtains or forges a ViewState blob → server decrypts/verifies using known machine keys → deserializes the object graph using a dangerous formatter (BinaryFormatter, etc.) → gadget chain (ObjectDataProvider, etc.) executes during deserialization or property setting.
- Preconditions:
  - Attacker can read or brute the machineKey values (hardcoded in web.config, in source, in backups, or weak defaults).
  - The app uses the legacy ViewState deserialization path without `enableViewStateMac` + strong keys + validation.
  - Or direct use of `BinaryFormatter.Deserialize` on attacker-influenced data.

## Chain Outline

1. **Collect ViewState sample** from a normal page response (hidden input).
2. **Decode / analyze** the ViewState (base64 → may need decryption if encrypted).
3. **Obtain machine keys**: From web.config, decompiled assemblies, misconfigured IIS, RCE on adjacent host, or known defaults for specific app versions (DNN).
4. **Generate malicious ViewState** using ysoserial.net with `ObjectDataProvider` (or other) gadget + desired command.
5. **Submit** the forged `__VIEWSTATE` (and usually matching `__VIEWSTATEGENERATOR` or other validators) via POST to a page that processes ViewState.
6. **Trigger deserial** on the server.
7. **Verify** RCE (ping, reverse PowerShell, webshell drop via command, etc.).

## Evidence

- Base64 ViewState from page + the crafted replacement.
- ysoserial.net command and output.
- Callback or command execution evidence.
- web.config snippet showing the keys used.

## Findings

### Root Cause
ViewState is a serialized object graph intended only for round-tripping UI state. When the validationKey/decryptionKey are known to the attacker, they can create a completely valid-looking malicious ViewState that the server will decrypt, validate the MAC, and then deserialize using the configured formatter — usually one that allows arbitrary gadget chains (BinaryFormatter is the classic villain here).

Hardcoded or disclosed keys in web.config (or derivable from other sources) completely break the security model.

```xml
<!-- DANGEROUS if keys are known -->
<machineKey validationKey="..." decryptionKey="..." validation="SHA1" decryption="AES" />
```

Many older apps (and some misconfigured newer ones) ship with or leak these.

### Gadget of Choice (ObjectDataProvider)

ysoserial.net `ObjectDataProvider` chain is the go-to for ViewState because it can invoke methods (including `Process.Start` or `cmd.exe /c ...`) via XAML / data binding abuse without needing many supporting assemblies.

See `guides/.NET-Deserialization-Guide.md` and the poc Notes for exact ysoserial.net invocation.

### Other .NET Deserial Vectors (Related)

- Direct `BinaryFormatter` on cookies, headers, or API bodies (DotNetNuke cookie deserial is another classic in this repo).
- JSON.NET `TypeNameHandling.All` or `Auto`.
- `JavaScriptSerializer` with certain gadgets.
- `XmlSerializer`, `DataContractSerializer`, `NetDataContractSerializer`.

### Fix Ideas (Strongly Recommended)

- **Never** hardcode machine keys in web.config for production. Use DPAPI or Azure Key Vault / external secret stores. Rotate them.
- Set `ViewStateEncryptionMode="Always"` + `enableViewStateMac="true"` (default in newer ASP.NET but verify).
- Move to ASP.NET Core + newer state management (not ViewState at all) or at least use signed/encrypted tokens that are not deserialized into object graphs.
- Prefer JSON + strict typing over BinaryFormatter / LosFormatter for any client-persisted state.
- If you must use ViewState, keep the machineKey secret and rotate on compromise.
- Update to .NET 4.8+ and enable `NetFx45_LegacySecurityPolicy` mitigations or use the latest deserial protections.

For direct formatters: use `BinaryFormatter` only with a custom `SerializationBinder` + full type whitelist. Better: stop using it.

## OSWE Exam Tips

- **ViewState is everywhere** in classic .NET WebForms — check every page source for `__VIEWSTATE`.
- If you find machineKey values (in web.config via LFI, source disclosure, or previous low-priv RCE), treat it as "game over" for deserial RCE.
- ysoserial.net is the equivalent of ysoserial for Java — know the common gadgets: `ObjectDataProvider`, `TextFormattingRunProperties`, etc.
- The `__VIEWSTATEGENERATOR` value (or similar) is often required for the MAC/validation to pass; tools usually handle generating the right one when you supply the keys.
- In white-box: search for `LosFormatter`, `ObjectStateFormatter`, `BinaryFormatter`, `machineKey`, `ViewStateUserKey`.
- Time: Key discovery can take time (or be given in the source). Once you have keys + ysoserial.net command, exploitation is fast.
- Reporting: Show the decoded original ViewState, the key material, the ysoserial command, the POST with malicious ViewState, and verification.

## References

- ysoserial.net: https://github.com/pwntester/ysoserial.net
- Black Hat "Friday the 13th: JSON Attacks" (Alvaro Muñoz & Oleksandr Mirosh)
- `guides/.NET-Deserialization-Guide.md` (detailed ViewState + formatter guidance)
- `poc-examples/dotnet-viewstate-deserialization/` (PoC + Notes)
- `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md` (sister vulnerability using cookies)
- DotNetNuke advisory for CVE-2017-9822

See the rich lab manual in the poc directory for concrete ysoserial.net usage, machine key extraction, and verification steps.
