package com.lifelog.app.ui

import android.Manifest
import android.content.Context
import android.media.MediaRecorder
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.io.File

@Composable
fun CaptureScreen(vm: LifeLogViewModel, onDone: () -> Unit, onError: (String) -> Unit) {
    var recording by remember { mutableStateOf(false) }
    var recorder by remember { mutableStateOf<MediaRecorder?>(null) }
    var recordingFile by remember { mutableStateOf<File?>(null) }
    val context = androidx.compose.ui.platform.LocalContext.current
    val state by vm.state.collectAsState()
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri ?: return@rememberLauncherForActivityResult
        vm.upload(context, uri, onDone, onError)
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            val file = File(context.cacheDir, "lifelog-${System.currentTimeMillis()}.m4a")
            recordingFile = file
            recorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            recording = true
        } else onError("Microphone permission is required to record a memory.")
    }
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Text("Capture a memory", style = MaterialTheme.typography.headlineSmall)
        Text("Record a thought or choose an audio file. LifeLog will transcribe it and return the important details.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Card { Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Button(onClick = {
                if (recording) {
                    recorder?.stop(); recorder?.release(); recorder = null; recording = false
                    recordingFile?.let { vm.uploadFile(it, "audio/mp4", onDone, onError) }
                } else permission.launch(Manifest.permission.RECORD_AUDIO)
            }, Modifier.fillMaxWidth()) {
                Icon(Icons.Default.Mic, null); Text(if (recording) "Stop and process" else "Record audio", Modifier.padding(start = 8.dp))
            }
            Button(onClick = { picker.launch("audio/*") }, enabled = !recording && !state.uploading, Modifier.fillMaxWidth()) {
                Icon(Icons.Default.UploadFile, null); Text("Choose audio file", Modifier.padding(start = 8.dp))
            }
            if (state.uploading) { CircularProgressIndicator(); Text("Transcribing and extracting your memory…") }
            state.lastUpload?.let { upload ->
                Text("Memory saved", color = MaterialTheme.colorScheme.primary)
                upload.extracted?.summary?.let { Text(it, style = MaterialTheme.typography.titleMedium) }
                upload.transcript?.let { Text(it, maxLines = 6, color = MaterialTheme.colorScheme.onSurfaceVariant) }
            }
        } }
    }
}
