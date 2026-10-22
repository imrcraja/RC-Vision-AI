package com.rcvisionai.app

import android.app.job.JobParameters
import android.app.job.JobService
import java.io.File
import java.io.FileOutputStream

/**
 * Creates a best-effort daily ZIP in app-private storage. Android may defer this job.
 * This lightweight export is not a model-training service and contains no model weights.
 */
class DailyLearningJobService : JobService() {
    override fun onStartJob(params: JobParameters): Boolean {
        Thread {
            try {
                val directory = File(filesDir, "daily-learning")
                if (!directory.exists() && !directory.mkdirs()) {
                    throw IllegalStateException("Could not create daily learning directory")
                }
                val target = File(directory, "RC-Vision-AI-Learning.zip")
                val temporary = File(directory, "RC-Vision-AI-Learning.zip.tmp")
                FileOutputStream(temporary).use { stream ->
                    LocalLearningPackage.writeZip(stream, LocalWorkspace(this).getPrompts())
                }
                if (target.exists() && !target.delete()) {
                    throw IllegalStateException("Could not replace previous daily ZIP")
                }
                if (!temporary.renameTo(target)) {
                    throw IllegalStateException("Could not finalize daily ZIP")
                }
            } catch (_: Exception) {
                // Keep the service quiet; the next scheduled run can try again.
            } finally {
                jobFinished(params, false)
            }
        }.start()
        return true
    }

    override fun onStopJob(params: JobParameters): Boolean = true
}
