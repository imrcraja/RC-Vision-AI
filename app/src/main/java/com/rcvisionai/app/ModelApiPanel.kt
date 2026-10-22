package com.rcvisionai.app

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import java.net.NetworkInterface

internal object ModelApiPanel {
    private val muted = Color.rgb(164, 174, 194)
    private val accent = Color.rgb(95, 145, 255)

    fun render(activity: Activity, host: LinearLayout) {
        host.addView(label(activity, "MODEL API SERVER", 12f, accent, true))
        host.addView(label(activity, "Ek device host banega; doosre device client ki tarah connect karenge. LAN mode same Wi-Fi/hotspot par chalega.", 13f, muted))
        val state = label(activity, if (ModelApiServer.isRunning()) "STATUS: RUNNING" else "STATUS: STOPPED", 14f, Color.WHITE, true)
        host.addView(state, params())
        val token = ModelApiServer.token(activity)
        val tokenView = label(activity, "Bearer token (private):\n$token", 12f, Color.WHITE)
        tokenView.setTextIsSelectable(true)
        host.addView(tokenView, params())
        host.addView(button(activity, "Copy API token") {
            val clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            clipboard.setPrimaryClip(ClipData.newPlainText("RC Vision AI API token", token))
            Toast.makeText(activity, "Token copied. Isse private rakho.", Toast.LENGTH_LONG).show()
        }, params())
        val address = localAddresses().ifEmpty { listOf("Wi-Fi/LAN IP available nahi hai; network connect karo.") }
        host.addView(label(activity, "LAN address examples:\n" + address.joinToString("\n") { "http://$it:8765" }, 12f, muted), params())
        host.addView(button(activity, if (ModelApiServer.isRunning()) "Stop API server" else "Start API server (port 8765)") {
            if (ModelApiServer.isRunning()) {
                ModelApiServer.stop()
                state.text = "STATUS: STOPPED"
                Toast.makeText(activity, "API server stopped.", Toast.LENGTH_SHORT).show()
            } else {
                ModelApiServer.start(activity) { message ->
                    activity.runOnUiThread {
                        state.text = if (ModelApiServer.isRunning()) "STATUS: RUNNING — port 8765" else message
                    }
                }
                state.text = if (ModelApiServer.isRunning()) "STATUS: RUNNING — port 8765" else "STATUS: STARTING / ERROR"
            }
        }, params())
        host.addView(label(activity, "Endpoints: GET /health, GET /v1/models, POST /v1/chat/completions. Chat endpoint returns 503 until our own local LLM runtime is connected. This is API plumbing only, not working model inference yet.", 12f, muted), params())
        host.addView(label(activity, "SECURITY: HTTP + bearer token is for trusted LAN testing only. Do not port-forward this port to the public internet. Online use should go through HTTPS with a secure tunnel/reverse proxy and stronger access controls. Keep the token private.", 12f, Color.rgb(255, 190, 110)), params())
    }

    private fun localAddresses(): List<String> = try {
        NetworkInterface.getNetworkInterfaces().toList().flatMap { network ->
            if (!network.isUp || network.isLoopback) emptyList()
            else network.inetAddresses.toList().filter { it is java.net.Inet4Address && !it.isLoopbackAddress }.map { it.hostAddress ?: "" }
        }.filter { it.isNotBlank() }.distinct()
    } catch (_: Exception) { emptyList() }

    private fun label(activity: Activity, value: String, size: Float, color: Int, bold: Boolean = false) =
        TextView(activity).apply {
            text = value; textSize = size; setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
            setPadding(2, 5, 2, 5)
        }

    private fun button(activity: Activity, value: String, action: () -> Unit) =
        Button(activity).apply { text = value; isAllCaps = false; setOnClickListener { action() } }

    private fun params() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
    ).apply { topMargin = 8 }
}
