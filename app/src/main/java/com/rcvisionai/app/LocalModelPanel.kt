package com.rcvisionai.app

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

/** Local-only research console. No network requests are made from this screen. */
internal object LocalModelPanel {
    private val muted = Color.rgb(164, 174, 194)
    private val accent = Color.rgb(95, 145, 255)

    fun render(activity: Activity, host: LinearLayout) {
        host.addView(label(activity, "RC Vision AI • Local Lab", 25f, Color.WHITE, true))
        host.addView(label(activity, "Apna original model. Is screen se koi third-party LLM/API call nahi hoti.", 14f, muted, false))
        val status = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(14, 14, 14, 14)
            background = rounded(Color.rgb(19, 24, 36))
        }
        status.addView(label(activity, "MODEL STATUS", 12f, accent, true))
        status.addView(label(activity, "Research trainer: repository mein available", 15f, Color.WHITE, true))
        status.addView(label(activity, "Android inference: abhi integrated nahi hai", 14f, muted, false))
        status.addView(label(activity, "Is APK mein trained checkpoint bundled nahi hai. Isliye fake AI response nahi dikhaya jayega.", 13f, muted, false))
        host.addView(status, matchWrap())

        val prompt = EditText(activity).apply {
            hint = "Apne local model ke liye prompt / training idea likho…"
            setHintTextColor(muted); setTextColor(Color.WHITE); textSize = 15f
            minLines = 3; maxLines = 7; gravity = Gravity.TOP
            setPadding(12, 12, 12, 12)
            background = rounded(Color.rgb(14, 18, 28))
        }
        host.addView(prompt, matchWrap())
        val output = TextView(activity).apply {
            text = "Task log yahan dikhega. Local model runtime connect hone ka wait hai."
            textSize = 13f; setTextColor(muted); setPadding(12, 12, 12, 12)
            background = rounded(Color.rgb(19, 24, 36))
        }
        host.addView(output, matchWrap())
        host.addView(Button(activity).apply {
            text = "Save prompt locally"; isAllCaps = false
            setOnClickListener {
                val value = prompt.text.toString().trim()
                if (value.isBlank()) Toast.makeText(activity, "Pehle prompt likho.", Toast.LENGTH_SHORT).show()
                else {
                    val prefs = activity.getSharedPreferences("rc_vision_local_lab", Activity.MODE_PRIVATE)
                    val old = prefs.getString("saved_prompts", "").orEmpty()
                    prefs.edit().putString("saved_prompts", (old + "\n" + value).trim().takeLast(20000)).apply()
                    output.text = "Saved locally ✓\nPrompt training notebook ke liye save hua. Model inference abhi unavailable hai."
                }
            }
        }, matchWrap())
        host.addView(Button(activity).apply {
            text = "Run own local LLM"; isAllCaps = false
            setOnClickListener {
                output.text = "STATUS: BLOCKED — Android app abhi trained checkpoint/runtime load nahi karti.\n\nNo API fallback will be used. Next: checkpoint import, local inference runtime aur benchmark tests."
            }
        }, matchWrap())
    }

    private fun label(activity: Activity, value: String, size: Float, color: Int, bold: Boolean) =
        TextView(activity).apply {
            text = value; textSize = size; setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
            setPadding(2, 3, 2, 5)
        }
    private fun rounded(color: Int) = GradientDrawable().apply { setColor(color); cornerRadius = 18f }
    private fun matchWrap() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
    ).apply { topMargin = 10 }
}
