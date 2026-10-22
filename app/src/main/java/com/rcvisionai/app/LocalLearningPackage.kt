package com.rcvisionai.app

import org.json.JSONArray
import org.json.JSONObject
import java.io.OutputStream
import java.security.MessageDigest
import java.time.Instant
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * Creates an explicit user-requested export of local workspace state.
 * It does not include model weights because no model runtime is installed in the app yet.
 */
object LocalLearningPackage {
    fun writeZip(output: OutputStream, prompts: List<String>) {
        val files = linkedMapOf<String, ByteArray>()
        files["memory.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("memories", JSONArray())
            .put("note", "Empty template; no automatic personal-memory inference is implemented."))
        files["knowledge.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("topics", JSONArray())
            .put("note", "Knowledge tracking is a planned feature; no trained model knowledge is exported."))
        files["skills.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("skills", JSONArray()))
        files["evaluation.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("tests", JSONArray()))
        files["learning-state/prompts.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("prompts", JSONArray(prompts))
            .put("note", "These are saved prompts, not verified memories or model weights."))
        files["session.json"] = jsonBytes(JSONObject()
            .put("schema_version", 1)
            .put("project", "RC Vision AI")
            .put("created_utc", Instant.now().toString())
            .put("source", "Android local workspace")
            .put("model_checkpoint_included", false))

        val fileManifest = JSONArray()
        files.forEach { (name, bytes) ->
            fileManifest.put(JSONObject()
                .put("path", name)
                .put("size_bytes", bytes.size)
                .put("sha256", sha256(bytes)))
        }
        val manifest = JSONObject()
            .put("schema_version", 1)
            .put("package", "RC Vision AI Local Learning Export")
            .put("created_utc", Instant.now().toString())
            .put("files", fileManifest)
            .put("important", "Contains saved prompts and empty learning templates only; no model checkpoint or automatic learned knowledge.")
        files["manifest.json"] = jsonBytes(manifest)

        ZipOutputStream(output).use { zip ->
            files.forEach { (name, bytes) ->
                zip.putNextEntry(ZipEntry("RC-Vision-AI-Learning/$name"))
                zip.write(bytes)
                zip.closeEntry()
            }
        }
    }

    private fun jsonBytes(json: JSONObject): ByteArray =
        (json.toString(2) + "\n").toByteArray(Charsets.UTF_8)

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
}
