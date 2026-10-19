package com.lifelog.app.data

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.longOrNull

/**
 * Lenient helpers so the app can talk to servers that return slightly
 * different shapes for the same endpoint (bare array vs wrapped object,
 * numeric vs string ids, real arrays vs stringified arrays).
 */
object Lenient {

    /** Read a string value regardless of whether it is a string, number or bool. */
    fun str(obj: JsonObject, vararg keys: String): String? {
        for (key in keys) {
            val element = obj[key] ?: continue
            val primitive = element as? JsonPrimitive ?: continue
            val content = primitive.content
            if (content.isNotBlank() && content != "null") return content
        }
        return null
    }

    /** Read a long value that may be encoded as number or numeric string. */
    fun long(obj: JsonObject, vararg keys: String): Long? {
        for (key in keys) {
            val element = obj[key] ?: continue
            val primitive = element as? JsonPrimitive ?: continue
            primitive.longOrNull?.let { return it }
            primitive.doubleOrNull?.let { return it.toLong() }
        }
        return null
    }

    fun double(obj: JsonObject, vararg keys: String): Double? {
        for (key in keys) {
            val element = obj[key] ?: continue
            val primitive = element as? JsonPrimitive ?: continue
            primitive.doubleOrNull?.let { return it }
        }
        return null
    }

    fun bool(obj: JsonObject, vararg keys: String): Boolean? {
        for (key in keys) {
            val element = obj[key] ?: continue
            val primitive = element as? JsonPrimitive ?: continue
            primitive.booleanOrNull?.let { return it }
        }
        return null
    }

    /**
     * Read a list of strings. Accepts a real JSON array, a stringified JSON array
     * (`"[\"a\"]"`), a single string, or a list of objects with a `name` field.
     */
    fun stringList(obj: JsonObject, vararg keys: String): List<String> {
        for (key in keys) {
            val element = obj[key] ?: continue
            val result = stringListFrom(element)
            if (result.isNotEmpty()) return result
        }
        return emptyList()
    }

    fun stringListFrom(element: JsonElement?): List<String> {
        if (element == null) return emptyList()
        return when (element) {
            is JsonArray -> element.mapNotNull { item ->
                when (item) {
                    is JsonPrimitive -> item.content.takeIf { it.isNotBlank() && it != "null" }
                    is JsonObject -> str(item, "name", "title", "value", "summary")
                    else -> null
                }
            }
            is JsonPrimitive -> {
                val raw = element.content
                if (raw.isBlank() || raw == "null") emptyList()
                else if (raw.startsWith("[")) {
                    runCatching {
                        val parsed = kotlinx.serialization.json.Json.parseToJsonElement(raw)
                        stringListFrom(parsed)
                    }.getOrDefault(emptyList())
                } else listOf(raw)
            }
            is JsonObject -> listOfNotNull(str(element, "name", "title", "value", "summary"))
        }
    }

    /** Extract a list of objects from either a bare array or a wrapped object key. */
    fun objectList(root: JsonElement?, vararg wrapperKeys: String): List<JsonObject> {
        if (root == null) return emptyList()
        when (root) {
            is JsonArray -> return root.mapNotNull { it as? JsonObject }
            is JsonObject -> {
                for (key in wrapperKeys) {
                    val child = root[key]
                    if (child is JsonArray) return child.mapNotNull { it as? JsonObject }
                }
                // Fall back to the first array-valued property.
                for (value in root.values) {
                    if (value is JsonArray) return value.mapNotNull { it as? JsonObject }
                }
            }
            else -> Unit
        }
        return emptyList()
    }

    /** Extract the single object from a response that may be wrapped or bare. */
    fun objectOf(root: JsonElement?, vararg wrapperKeys: String): JsonObject? {
        if (root is JsonObject) {
            for (key in wrapperKeys) {
                val child = root[key]
                if (child is JsonObject) return child
            }
            return root
        }
        return null
    }
}
