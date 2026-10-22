package com.rcvisionai.app

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.View
import android.view.ViewGroup
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/** OpenRouter chat client. Credentials are used in memory only and are never written to disk. */
internal object OpenRouterChatPanel {
    private const val ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    private val muted = Color.rgb(164, 174, 194)
    private val accent = Color.rgb(95, 145, 255)

    fun render(activity: Activity, host: LinearLayout) {
        host.addView(label(activity, "RC Vision Chat", 25f, Color.WHITE, true))
        host.addView(label(activity, "Online API chat. Save karne par key Android Keystore se encrypted form mein device par rahegi.", 14f, muted, false))
        val key = field(activity, "OpenRouter API key", true).apply { setText(ApiKeyVault.load(activity).orEmpty()) }
        val model = field(activity, "Model ID", false).apply { setText("openrouter/auto") }
        host.addView(label(activity, "PRIVATE API KEY", 12f, accent, true))
        host.addView(key, matchWrap())
        val keyActions = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        val saveKey = Button(activity).apply {
            text = "Save encrypted key"; isAllCaps = false
            setOnClickListener {
                val value = key.text.toString().trim()
                if (!value.startsWith("sk-or-")) {
                    addLine(activity, transcriptPlaceholder(activity), "Status", "OpenRouter key format check karo.")
                } else {
                    try {
                        ApiKeyVault.save(activity, value)
                        android.widget.Toast.makeText(activity, "Key device par encrypted save ho gayi.", android.widget.Toast.LENGTH_LONG).show()
                    } catch (e: Exception) {
                        android.widget.Toast.makeText(activity, "Key save fail: ${e.message}", android.widget.Toast.LENGTH_LONG).show()
                    }
                }
            }
        }
        val forgetKey = Button(activity).apply {
            text = "Forget key"; isAllCaps = false
            setOnClickListener {
                ApiKeyVault.clear(activity); key.setText("")
                android.widget.Toast.makeText(activity, "Saved key clear ho gayi.", android.widget.Toast.LENGTH_SHORT).show()
            }
        }
        keyActions.addView(saveKey, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        keyActions.addView(forgetKey, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        host.addView(keyActions, matchWrap())
        host.addView(label(activity, "MODEL ID", 12f, accent, true))
        host.addView(model, matchWrap())

        val transcript = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(12, 12, 12, 12)
            background = rounded(Color.rgb(19, 24, 36))
        }
        val scroll = ScrollView(activity).apply { addView(transcript) }
        host.addView(scroll, LinearLayout.LayoutParams(-1, 500).apply { topMargin = 12; bottomMargin = 10 })
        val prompt = field(activity, "Message likho…", false).apply { minLines = 2; maxLines = 5; gravity = Gravity.TOP }
        host.addView(prompt, matchWrap())
        val send = Button(activity).apply {
            text = "Send to OpenRouter"; isAllCaps = false; setTextColor(Color.WHITE); background = rounded(accent)
        }
        host.addView(send, matchWrap())
        val messages = JSONArray()
        var busy = false
        send.setOnClickListener {
            if (busy) return@setOnClickListener
            val token = key.text.toString().trim()
            val modelId = model.text.toString().trim().ifEmpty { "openrouter/auto" }
            val userText = prompt.text.toString().trim()
            if (token.isBlank()) { addLine(activity, transcript, "Status", "OpenRouter API key enter karo."); return@setOnClickListener }
            if (userText.isBlank()) { addLine(activity, transcript, "Status", "Pehle message likho."); return@setOnClickListener }
            messages.put(JSONObject().put("role", "user").put("content", userText))
            addLine(activity, transcript, "You", userText)
            prompt.setText("")
            busy = true; send.isEnabled = false; send.text = "Waiting…"
            thread(name = "openrouter-chat") {
                val (answer, error) = request(token, modelId, messages)
                activity.runOnUiThread {
                    if (answer != null) {
                        messages.put(JSONObject().put("role", "assistant").put("content", answer))
                        transcript.removeAllViews()
                        for (i in 0 until messages.length()) {
                            val item = messages.optJSONObject(i) ?: continue
                            addLine(activity, transcript, if (item.optString("role") == "user") "You" else "RC Vision AI", item.optString("content"))
                        }
                    } else addLine(activity, transcript, "API error", error ?: "Unknown error")
                    scroll.post { scroll.fullScroll(View.FOCUS_DOWN) }
                    busy = false; send.isEnabled = true; send.text = "Send to OpenRouter"
                }
            }
        }
        host.addView(label(activity, "Note: yeh API chat hai. Is build mein abhi isolated code sandbox / tool execution connected nahi hai.", 12f, muted, false))
    }

    private fun transcriptPlaceholder(activity: Activity) = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }\n\n    private fun request(token: String, model: String, messages: JSONArray): Pair<String?, String?> {
        var conn: HttpURLConnection? = null
        return try {
            conn = (URL(ENDPOINT).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"; connectTimeout = 20000; readTimeout = 60000; doOutput = true
                setRequestProperty("Authorization", "Bearer $token")
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("HTTP-Referer", "https://github.com/imrcraja/RC-Vision-AI")
                setRequestProperty("X-Title", "RC Vision AI")
            }
            val payload = JSONObject().put("model", model).put("messages", messages).put("temperature", 0.7).toString()
            conn.outputStream.use { it.write(payload.toByteArray(Charsets.UTF_8)) }
            val status = conn.responseCode
            val stream = if (status in 200..299) conn.inputStream else conn.errorStream
            val raw = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            val json = JSONObject(raw)
            if (status !in 200..299) null to (json.optJSONObject("error")?.optString("message") ?: "HTTP $status")
            else {
                val value = json.optJSONArray("choices")?.optJSONObject(0)?.optJSONObject("message")?.optString("content")
                if (value.isNullOrBlank()) null to "Empty response from API" else value to null
            }
        } catch (e: Exception) {
            null to "${e.javaClass.simpleName}: ${e.message ?: "network error"}"
        } finally { conn?.disconnect() }
    }

    private fun addLine(a: Activity, host: LinearLayout, who: String, value: String) {
        host.addView(label(a, who, 12f, accent, true))
        host.addView(label(a, value, 14f, Color.WHITE, false).apply { setPadding(2, 2, 2, 12) })
    }
    private fun field(a: Activity, hintText: String, secret: Boolean) = EditText(a).apply {
        hint = hintText; setHintTextColor(muted); setTextColor(Color.WHITE); setPadding(14, 12, 14, 12)
        background = rounded(Color.rgb(22, 28, 42)); isSingleLine = !secret
        if (secret) inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
    }
    private fun label(a: Activity, value: String, size: Float, color: Int, bold: Boolean) = TextView(a).apply {
        text = value; textSize = size; setTextColor(color); if (bold) setTypeface(typeface, Typeface.BOLD)
        setPadding(2, 4, 2, 4); textIsSelectable = true
    }
    private fun rounded(color: Int) = GradientDrawable().apply { setColor(color); cornerRadius = 18f }
    private fun matchWrap() = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
}
