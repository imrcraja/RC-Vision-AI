package com.rcvisionai.app

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.graphics.drawable.RippleDrawable
import android.content.res.ColorStateList
import android.content.Intent
import android.view.animation.DecelerateInterpolator
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private val bg = Color.rgb(12, 15, 23)
    private val panel = Color.rgb(23, 28, 40)
    private val accent = Color.rgb(95, 145, 255)
    private val muted = Color.rgb(164, 174, 194)
    private lateinit var root: LinearLayout
    private lateinit var body: LinearLayout
    private lateinit var workspace: LocalWorkspace
    private var currentTab = "Create"
    private val exportRequestCode = 4201

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        workspace = LocalWorkspace(this)
        DailyLearningScheduler.schedule(this)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        window.decorView.systemUiVisibility = 0
        showScreen("Create")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != exportRequestCode || resultCode != RESULT_OK) return
        val uri = data?.data ?: return
        try {
            val stream = contentResolver.openOutputStream(uri)
            if (stream == null) {
                Toast.makeText(this, "ZIP file open nahi ho saki.", Toast.LENGTH_LONG).show()
                return
            }
            LocalLearningPackage.writeZip(stream, workspace.getPrompts())
            Toast.makeText(this, "Local learning ZIP export ho gaya.", Toast.LENGTH_LONG).show()
        } catch (error: Exception) {
            Toast.makeText(this, "Export fail hua: ${error.message ?: "unknown error"}", Toast.LENGTH_LONG).show()
        }
    }

    private fun requestLearningExport() {
        val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "application/zip"
            putExtra(Intent.EXTRA_TITLE, "RC-Vision-AI-Learning.zip")
        }
        startActivityForResult(intent, exportRequestCode)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun rounded(color: Int, radius: Int = 18): GradientDrawable =
        GradientDrawable().apply {
            setColor(color)
            cornerRadius = dp(radius).toFloat()
        }

    /** Lightweight liquid-glass-inspired surface: translucent gradient, cool edge and soft highlight. */
    private fun glassSurface(): GradientDrawable =
        GradientDrawable(
            GradientDrawable.Orientation.TL_BR,
            intArrayOf(Color.rgb(38, 48, 68), Color.rgb(23, 29, 43), Color.rgb(18, 23, 35))
        ).apply {
            cornerRadius = dp(22).toFloat()
            setStroke(dp(1), Color.argb(105, 167, 196, 255))
        }

    private fun animateIn(view: View, delay: Long = 0L) {
        view.alpha = 0f
        view.translationY = dp(12).toFloat()
        AnimatorSet().apply {
            playTogether(
                ObjectAnimator.ofFloat(view, View.ALPHA, 0f, 1f),
                ObjectAnimator.ofFloat(view, View.TRANSLATION_Y, dp(12).toFloat(), 0f)
            )
            duration = 320
            startDelay = delay
            interpolator = DecelerateInterpolator()
            start()
        }
    }

    private fun text(value: String, size: Float, color: Int = Color.WHITE, bold: Boolean = false): TextView =
        TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
            setPadding(dp(2), dp(3), dp(2), dp(3))
        }

    private fun button(label: String, action: () -> Unit): Button =
        Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 14f
            setTextColor(Color.WHITE)
            background = RippleDrawable(ColorStateList.valueOf(Color.argb(55, 255, 255, 255)), rounded(accent, 14), rounded(Color.WHITE, 14))
            elevation = dp(2).toFloat()
            setPadding(dp(12), dp(5), dp(12), dp(5))
            setOnClickListener { action() }
        }

    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(15), dp(16), dp(15))
        background = glassSurface()
        elevation = dp(3).toFloat()
        layoutParams = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { bottomMargin = dp(12) }
    }

    private fun showScreen(tab: String) {
        currentTab = tab
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                intArrayOf(Color.rgb(10, 15, 28), Color.rgb(17, 22, 35), Color.rgb(10, 13, 22))
            )
            setPadding(dp(18), dp(14), dp(18), dp(8))
        }
        setContentView(root)

        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        brand.addView(text("RC VISION AI", 22f, Color.WHITE, true))
        brand.addView(text("PRIVATE • LOCAL-FIRST • IN DEVELOPMENT", 10f, muted))
        header.addView(brand, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        header.addView(text("v0.1.0", 12f, muted))
        root.addView(header)

        val scroll = ScrollView(this)
        body = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(18), 0, dp(12))
        }
        scroll.addView(body)
        root.addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))

        when (tab) {
            "Create" -> createPage()
            "Chat" -> chatPage()
            "Train" -> trainPage()
            else -> settingsPage()
        }
        for (i in 0 until body.childCount) animateIn(body.getChildAt(i), (i * 55L).coerceAtMost(220L))

        val nav = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(0, dp(6), 0, dp(2))
        }
        listOf("Create", "Chat", "Train", "Settings").forEach { name ->
            val item = TextView(this).apply {
                text = if (name == tab) "●  $name" else name
                textSize = 12f
                gravity = Gravity.CENTER
                setTextColor(if (name == tab) Color.WHITE else muted)
                setPadding(dp(7), dp(12), dp(7), dp(12))
                if (name == tab) background = rounded(Color.rgb(41, 61, 96), 16)
                setOnClickListener { showScreen(name) }
            }
            nav.addView(item, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        }
        root.addView(nav)
    }

    private fun createPage() {
        body.addView(text("Create something original.", 25f, Color.WHITE, true))
        body.addView(text("Your prompt workspace is ready. The original image model is not trained yet, so this build will not pretend to generate images.", 14f, muted).apply {
            setPadding(dp(2), dp(6), dp(2), dp(18))
        })

        val promptCard = card()
        promptCard.addView(text("IMAGE PROMPT", 12f, accent, true))
        val prompt = EditText(this).apply {
            hint = "Describe the image you want to create…"
            setHintTextColor(muted)
            setTextColor(Color.WHITE)
            textSize = 16f
            gravity = Gravity.TOP
            minLines = 5
            maxLines = 9
            setPadding(dp(12), dp(12), dp(12), dp(12))
            background = rounded(Color.rgb(14, 18, 28), 12)
            setText(workspace.latestPrompt())
        }
        promptCard.addView(prompt, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = dp(10) })
        val actions = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(10), 0, 0)
        }
        actions.addView(button("Save prompt") {
            val value = prompt.text.toString().trim()
            if (value.isEmpty()) {
                Toast.makeText(this, "Pehle prompt likho.", Toast.LENGTH_SHORT).show()
            } else {
                workspace.savePrompt(value)
                Toast.makeText(this, "Prompt is device par save ho gaya.", Toast.LENGTH_SHORT).show()
            }
        }, LinearLayout.LayoutParams(0, dp(48), 1f))
        actions.addView(View(this), LinearLayout.LayoutParams(dp(8), 1))
        actions.addView(button("Generate") {
            val value = prompt.text.toString().trim()
            if (value.isEmpty()) {
                Toast.makeText(this, "Pehle prompt likho.", Toast.LENGTH_SHORT).show()
            } else {
                workspace.savePrompt(value)
                Toast.makeText(this, "Original image model abhi develop/train hona baaki hai. Koi fake output nahi banaya.", Toast.LENGTH_LONG).show()
            }
        }, LinearLayout.LayoutParams(0, dp(48), 1f))
        promptCard.addView(actions)
        body.addView(promptCard)

        val status = card()
        status.addView(text("ENGINE STATUS", 12f, accent, true))
        status.addView(text("LLM core", 16f, Color.WHITE, true))
        status.addView(text("Research trainer implemented; no trained LLM bundled or loaded in this app.", 13f, muted))
        status.addView(text("Image generation", 16f, Color.WHITE, true).apply { setPadding(0, dp(10), 0, 0) })
        status.addView(text("Not available until a trained original model exists.", 13f, muted))
        body.addView(status)

        val history = card()
        history.addView(text("RECENT PROMPTS", 12f, accent, true))
        val prompts = workspace.getPrompts().take(5)
        if (prompts.isEmpty()) {
            history.addView(text("Saved prompts will appear here.", 13f, muted))
        } else {
            prompts.forEach { saved ->
                val item = text("•  $saved", 13f, Color.WHITE)
                item.setOnClickListener {
                    prompt.setText(saved)
                    prompt.setSelection(prompt.text.length)
                }
                history.addView(item)
            }
        }
        body.addView(history)
    }

    private fun chatPage() {
        LocalModelPanel.render(this, body)
        val local = card()
        local.addView(text("LOCAL MODEL STATUS", 12f, accent, true))
        local.addView(text("Original LLM hamara khud ka model hai. Koi third-party LLM API ya cloud fallback use nahi hota. Android inference abhi integrate hona baaki hai.", 13f, muted))
        body.addView(local)
    }

    private fun trainPage() {
        body.addView(text("Training Lab", 25f, Color.WHITE, true))
        body.addView(text("A safe place to inspect the project pipeline. A small CPU research run is configured in GitHub Actions; this Android app itself does not train a model.", 14f, muted))
        val c = card()
        c.addView(text("TRAINING PIPELINE", 12f, accent, true))
        c.addView(text("✓ 1. Dataset manifest and permission metadata", 14f))
        c.addView(text("✓ 2. Original LLM architecture prototype", 14f))
        c.addView(text("3. Train/evaluate checkpoints (research run)", 14f))
        c.addView(text("4. Integrate and evaluate on target Android devices", 14f))
        c.addView(text("Training is compute-intensive. The app must measure actual device capability before attempting any heavy job.", 13f, muted))
        body.addView(c)
    }

    private fun settingsPage() {
        body.addView(text("Settings & privacy", 25f, Color.WHITE, true))
        val c = card()
        c.addView(text("LOCAL DATA", 12f, accent, true))
        c.addView(text("Saved prompts stay in app-private storage. OpenRouter chat uses Internet only when you send a request; saved API keys are encrypted with Android Keystore.", 14f, muted))
        c.addView(button("Clear saved prompts") {
            workspace.clearPrompts()
            Toast.makeText(this, "Saved prompts cleared.", Toast.LENGTH_SHORT).show()
            showScreen("Settings")
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(48)).apply {
            topMargin = dp(14)
        })
        DeviceMonitorPanel.render(this, c)
        body.addView(c)

        val export = card()
        export.addView(text("LEARNING EXPORT", 12f, accent, true))
        export.addView(text("A best-effort daily job saves a ZIP in app-private storage after you first open the app. Export saved prompts and empty learning templates to a chosen location for review. No trained model weights or inferred memories are included yet.", 14f, muted))
        export.addView(button("Export local learning ZIP") {
            requestLearningExport()
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(48)).apply {
            topMargin = dp(12)
        })
        body.addView(export)

        val about = card()
        about.addView(text("ABOUT RC VISION AI", 12f, accent, true))
        about.addView(text("Independent project. OpenRouter can power online chat when configured. The original local LLM and rendering engines remain research prototypes.", 14f, Color.WHITE))
        about.addView(text("Version 0.1.0 • Runtime foundation only", 12f, muted))
        body.addView(about)
    }
}
