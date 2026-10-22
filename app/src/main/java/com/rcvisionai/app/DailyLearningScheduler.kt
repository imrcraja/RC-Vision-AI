package com.rcvisionai.app

import android.app.job.JobInfo
import android.app.job.JobScheduler
import android.content.ComponentName
import android.content.Context
import java.util.concurrent.TimeUnit

/** Schedules a best-effort daily local export after the user opens the app. */
object DailyLearningScheduler {
    private const val JOB_ID = 82041

    fun schedule(context: Context) {
        val scheduler = context.getSystemService(Context.JOB_SCHEDULER_SERVICE) as JobScheduler
        if (scheduler.getPendingJob(JOB_ID) != null) return
        val job = JobInfo.Builder(
            JOB_ID,
            ComponentName(context, DailyLearningJobService::class.java)
        )
            .setPeriodic(TimeUnit.DAYS.toMillis(1))
            .setPersisted(false)
            .build()
        scheduler.schedule(job)
    }
}
