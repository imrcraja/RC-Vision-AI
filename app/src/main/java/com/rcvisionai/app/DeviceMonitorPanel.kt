package com.rcvisionai.app

import android.app.Activity
import android.app.ActivityManager
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.os.BatteryManager
import android.os.Build
import android.os.Choreographer
import android.os.PowerManager
import android.os.SystemClock
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import java.util.Locale

/** Lightweight on-demand device monitor. Values are estimates and platform-visible readings only. */
internal object DeviceMonitorPanel {
    private val accent = Color.rgb(95, 145, 255)
    private val muted = Color.rgb(164, 174, 194)

    fun render(activity: Activity, host: LinearLayout) {
        host.addView(label(activity, "DEVICE PERFORMANCE", 12f, accent, true))
        host.addView(label(activity, "Readings refresh only when requested. Android does not expose reliable CPU temperature or every app/game's real FPS to ordinary apps.", 13f, muted, false))
        val output = label(activity, "Tap Refresh to read available device metrics.", 14f, Color.WHITE, false)
        host.addView(output)
        val row = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        val refresh = Button(activity).apply {
            text = "Refresh metrics"; isAllCaps = false
            setOnClickListener { output.text = readMetrics(activity) }
        }
        val fps = Button(activity).apply {
            text = "Estimate UI FPS"; isAllCaps = false
            setOnClickListener {
                text = "Measuring…"
                estimateUiFps(activity) { value ->
                    output.text = readMetrics(activity) + "\nUI frame estimate: $value FPS (short sample; not game/render FPS)"
                    text = "Estimate UI FPS"
                }
            }
        }
        row.addView(refresh, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        row.addView(fps, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        host.addView(row)
    }

    private fun readMetrics(activity: Activity): String {
        val runtime = Runtime.getRuntime()
        val usedMb = (runtime.totalMemory() - runtime.freeMemory()) / (1024 * 1024)
        val maxMb = runtime.maxMemory() / (1024 * 1024)
        val am = activity.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val info = ActivityManager.MemoryInfo()
        am.getMemoryInfo(info)
        val totalMb = info.totalMem / (1024 * 1024)
        val availMb = info.availMem / (1024 * 1024)
        val battery = activity.registerReceiver(null, android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED))
        val tempTenths = battery?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
        val batteryTemp = if (tempTenths >= 0) String.format(Locale.US, "%.1f°C", tempTenths / 10.0) else "Unavailable"
        val pm = activity.getSystemService(Context.POWER_SERVICE) as PowerManager
        val thermal = if (Build.VERSION.SDK_INT >= 29) {
            when (pm.currentThermalStatus) {
                PowerManager.THERMAL_STATUS_NONE -> "Normal"
                PowerManager.THERMAL_STATUS_LIGHT -> "Light"
                PowerManager.THERMAL_STATUS_MODERATE -> "Moderate"
                PowerManager.THERMAL_STATUS_SEVERE -> "Severe"
                PowerManager.THERMAL_STATUS_CRITICAL -> "Critical"
                PowerManager.THERMAL_STATUS_EMERGENCY -> "Emergency"
                PowerManager.THERMAL_STATUS_SHUTDOWN -> "Shutdown"
                else -> "Unknown"
            }
        } else "API unavailable (Android < 10)"
        return "App heap: $usedMb MB used / $maxMb MB limit\nDevice RAM: $availMb MB available / $totalMb MB total\nBattery temperature: $batteryTemp\nAndroid thermal status: $thermal\nCPU temperature: not exposed reliably by standard Android API\nStorage / GPU load: not sampled in this prototype"
    }

    private fun estimateUiFps(activity: Activity, done: (Int) -> Unit) {
        val choreographer = Choreographer.getInstance()
        var frames = 0
        val start = SystemClock.elapsedRealtimeNanos()
        val callback = object : Choreographer.FrameCallback {
            override fun doFrame(frameTimeNanos: Long) {
                frames++
                val elapsed = frameTimeNanos - start
                if (elapsed >= 1_000_000_000L) {
                    done((frames * 1_000_000_000.0 / elapsed).toInt().coerceAtLeast(0))
                } else choreographer.postFrameCallback(this)
            }
        }
        choreographer.postFrameCallback(callback)
    }

    private fun label(a: Activity, value: String, size: Float, color: Int, bold: Boolean) =
        TextView(a).apply {
            text = value; textSize = size; setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
            setPadding(2, 5, 2, 7); textIsSelectable = true
        }
}
