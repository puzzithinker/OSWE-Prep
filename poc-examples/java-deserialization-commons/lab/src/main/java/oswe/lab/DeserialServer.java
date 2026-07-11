package oswe.lab;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.*;
import java.net.InetSocketAddress;
import java.util.Base64;

/**
 * OSWE-LAB: Java HTTP server that deserializes POST body or base64 cookie.
 * Commons Collections 3.2.1 on classpath for ysoserial gadgets.
 */
public class DeserialServer {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/", new IndexHandler());
        server.createContext("/vulnerable", new DeserialHandler());
        server.createContext("/health", ex -> {
            byte[] b = "{\"status\":\"ok\"}".getBytes();
            ex.getResponseHeaders().add("Content-Type", "application/json");
            ex.sendResponseHeaders(200, b.length);
            ex.getResponseBody().write(b);
            ex.close();
        });
        server.start();
        System.out.println("java-deserial lab on 8080");
    }

    static class IndexHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            String body = "<h1>OSWE-LAB Java Deserialization</h1>"
                    + "<p>POST raw serialized bytes to <code>/vulnerable</code> "
                    + "or cookie <code>session=BASE64</code>.</p>"
                    + "<p>Commons Collections 3.2.1 present. Flag: /flag.txt</p>";
            byte[] b = body.getBytes();
            ex.getResponseHeaders().add("Content-Type", "text/html");
            ex.sendResponseHeaders(200, b.length);
            ex.getResponseBody().write(b);
            ex.close();
        }
    }

    static class DeserialHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                InputStream in = ex.getRequestBody();
                byte[] body = readAll(in);
                if (body.length == 0) {
                    String cookie = ex.getRequestHeaders().getFirst("Cookie");
                    if (cookie != null && cookie.contains("session=")) {
                        String b64 = cookie.split("session=")[1].split(";")[0].trim();
                        body = Base64.getDecoder().decode(b64);
                    }
                }
                if (body.length > 0) {
                    ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(body));
                    // VULNERABLE
                    Object o = ois.readObject();
                    ois.close();
                    System.out.println("Deserialized: " + o);
                }
                byte[] resp = "OK deserialized\n".getBytes();
                ex.sendResponseHeaders(200, resp.length);
                ex.getResponseBody().write(resp);
            } catch (Throwable t) {
                byte[] resp = ("ERR " + t.getClass().getSimpleName() + ": " + t.getMessage()).getBytes();
                ex.sendResponseHeaders(500, resp.length);
                ex.getResponseBody().write(resp);
            }
            ex.close();
        }
    }

    static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) != -1) bos.write(buf, 0, n);
        return bos.toByteArray();
    }
}
