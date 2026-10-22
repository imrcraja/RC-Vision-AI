package com.rcvisionai.app

import android.content.Context
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.net.ServerSocket
import java.net.Socket
import java.security.SecureRandom
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Small authenticated HTTP API foundation for LAN access.
 * Chat requests deliberately return 503 until the original local model runtime is integrated.
 * Plain HTTP is suitable only for a trusted LAN; do not expose this port directly to the public internet.
 */
internal object ModelApiServer {
    private val running = AtomicBoolean(false)
    @Volatile private var serverSocket: ServerSocket? = null
    @Volatile private var worker: Thread? = null
    @Volatile private var activeToken: String = ""

    fun isRunning(): Boolean = running.get()
    fun token(context: Context): String {
        val prefs = context.getSharedPreferences("rc_vision_api_server", Context.MODE_PRIVATE)
        val saved = prefs.getString("bearer_token", null)
        if (!saved.isNullOrBlank()) return saved
        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        val created = bytes.joinToString("") { "%02x".format(it) }
        prefs.edit().putString("bearer_token", created).apply()
        return created
    }

    @Synchronized fun start(context: Context, port: Int = 8765, onStatus: (String) -> Unit) {
        if (running.get()) { onStatus("Server already running on port $port"); return }
        val token = token(context)
        try {
            val socket = ServerSocket(port, 16, java.net.InetAddress.getByName("0.0.0.0"))
            serverSocket = socket
            activeToken = token
            running.set(true)
            worker = Thread {
                onStatus("API server running on port $port")
                while (running.get()) {
                    try {
                        val client = socket.accept()
                        Thread { handle(client, token) }.start()
                    } catch (e: Exception) {
                        if (running.get()) onStatus("API server error: ${e.message ?: "unknown"}")
                    }
                }
            }.apply { name = "RCVision-API-Accept"; isDaemon = true; start() }
        } catch (e: Exception) {
            running.set(false)
            onStatus("Could not start server: ${e.message ?: "unknown error"}")
        }
    }

    @Synchronized fun stop() {
        running.set(false)
        try { serverSocket?.close() } catch (_: Exception) {}
        serverSocket = null
        worker = null
    }

    private fun handle(socket: Socket, token: String) {
        socket.use { client ->
            client.soTimeout = 5000
            val input = BufferedInputStream(client.getInputStream())
            val output = BufferedOutputStream(client.getOutputStream())
            try {
                val firstLine = readLine(input, 8192) ?: return
                val parts = firstLine.split(" ")
                if (parts.size < 2) { respond(output, 400, "Bad Request", JSONObject().put("error", "bad_request")); return }
                val method = parts[0]
                val path = parts[1].substringBefore("?")
                var contentLength = 0
                var authorization = ""
                while (true) {
                    val line = readLine(input, 8192) ?: break
                    if (line.isEmpty()) break
                    val colon = line.indexOf(':')
                    if (colon <= 0) continue
                    val key = line.substring(0, colon).trim().lowercase()
                    val value = line.substring(colon + 1).trim()
                    if (key == "authorization") authorization = value
                    if (key == "content-length") contentLength = value.toIntOrNull() ?: 0
                }
                if (contentLength > 1_048_576 || contentLength < 0) {
                    respond(output, 413, "Payload Too Large", JSONObject().put("error", "body_too_large")); return
                }
                val body = ByteArray(contentLength)
                var offset = 0
                while (offset < contentLength) {
                    val count = input.read(body, offset, contentLength - offset)
                    if (count < 0) break
                    offset += count
                }
                if (authorization != "Bearer $token") {
                    respond(output, 401, "Unauthorized", JSONObject().put("error", "unauthorized")); return
                }
                when {
                    method == "GET" && path == "/health" ->
                        respond(output, 200, "OK", JSONObject().put("ok", true).put("service", "rc-vision-ai").put("inference_ready", false))
                    method == "GET" && path == "/v1/models" ->
                        respond(output, 200, "OK", JSONObject().put("object", "list").put("data", org.json.JSONArray().put(JSONObject().put("id", "rc-vision-local").put("object", "model").put("status", "runtime_not_integrated"))))
                    method == "POST" && path == "/v1/chat/completions" ->
                        respond(output, 503, "Service Unavailable", JSONObject().put("error", JSONObject().put("type", "model_runtime_unavailable").put("message", "RC Vision AI local inference runtime is not integrated yet. No external API fallback is used.")))
                    else -> respond(output, 404, "Not Found", JSONObject().put("error", "not_found"))
                }
            } catch (e: Exception) {
                try { respond(output, 400, "Bad Request", JSONObject().put("error", "bad_request")) } catch (_: Exception) {}
            }
        }
    }

    private fun readLine(input: BufferedInputStream, max: Int): String? {
        val bytes = java.io.ByteArrayOutputStream()
        while (bytes.size() < max) {
            val b = input.read()
            if (b < 0) return if (bytes.size() == 0) null else bytes.toString("UTF-8")
            if (b == 10) break
            if (b != 13) bytes.write(b)
        }
        return bytes.toString("UTF-8")
    }

    private fun respond(output: BufferedOutputStream, code: Int, reason: String, json: JSONObject) {
        val bytes = json.toString().toByteArray(Charsets.UTF_8)
        val headers = "HTTP/1.1 $code $reason\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: ${bytes.size}\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n"
        output.write(headers.toByteArray(Charsets.UTF_8))
        output.write(bytes)
        output.flush()
    }
}
