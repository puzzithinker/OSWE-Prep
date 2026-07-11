using System.Diagnostics;
using Newtonsoft.Json;

// OSWE-LAB: insecure JSON deserialization with TypeNameHandling.All
// (ViewState/ysoserial.net still best practiced on Windows; this lab teaches .NET gadget mindset)

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => Results.Content("""
<!DOCTYPE html>
<html><body>
<h1>OSWE-LAB · .NET JSON Deserialization</h1>
<p>POST JSON to <code>/api/parse</code> with Newtonsoft <code>TypeNameHandling.All</code>.</p>
<p>Classic dangerous type: <code>System.Windows.Data.ObjectDataProvider</code> may not load on Linux ASP.NET.</p>
<p>This lab also accepts a simplified gadget DTO with <code>$type</code> pointing at
<code>OsweLab.EvilCommand, DotNetLab</code> for reliable Linux RCE practice.</p>
<pre>
{"$type":"OsweLab.EvilCommand, DotNetLab","Cmd":"id"}
</pre>
<p>Flag: /flag.txt</p>
</body></html>
""", "text/html"));

app.MapPost("/api/parse", async (HttpRequest req) =>
{
    using var reader = new StreamReader(req.Body);
    var json = await reader.ReadToEndAsync();
    var settings = new JsonSerializerSettings
    {
        // VULNERABLE
        TypeNameHandling = TypeNameHandling.All
    };
    try
    {
        var obj = JsonConvert.DeserializeObject(json, settings);
        if (obj is OsweLab.EvilCommand evil)
        {
            evil.Run();
        }
        return Results.Ok(new { status = "deserialized", type = obj?.GetType().FullName });
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();

namespace OsweLab
{
    public class EvilCommand
    {
        public string Cmd { get; set; } = "id";
        public void Run()
        {
            // Invoked when type is constructed/deserialized path uses property then Run from endpoint
            var p = Process.Start(new ProcessStartInfo
            {
                FileName = "/bin/sh",
                Arguments = $"-c \"{Cmd}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true
            });
            p?.WaitForExit(5000);
        }
    }
}
