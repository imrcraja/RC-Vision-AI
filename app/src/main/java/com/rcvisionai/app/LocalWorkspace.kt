package com.rcvisionai.app

import android.content.Context

/**
 * Local-only workspace. It stores prompt history on this device and performs no network I/O.
 */
class LocalWorkspace(context: Context) {
    private val prefs = context.getSharedPreferences("rc_vision_workspace", Context.MODE_PRIVATE)

    fun savePrompt(prompt: String) {
        val cleaned = prompt.trim()
        if (cleaned.isEmpty()) return
        val history = getPrompts().toMutableList()
        history.remove(cleaned)
        history.add(0, cleaned)
        prefs.edit().putStringSet("prompts", history.take(30).toSet()).apply()
        prefs.edit().putString("latest_prompt", cleaned).apply()
    }

    fun latestPrompt(): String = prefs.getString("latest_prompt", "") ?: ""

    fun getPrompts(): List<String> {
        val latest = latestPrompt()
        val saved = prefs.getStringSet("prompts", emptySet()).orEmpty().toList()
        return (listOf(latest).filter { it.isNotBlank() } + saved.filter { it != latest }).take(30)
    }

    fun clearPrompts() {
        prefs.edit().remove("prompts").remove("latest_prompt").apply()
    }
}
