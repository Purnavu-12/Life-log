package com.lifelog.app.ui

import android.Manifest
import android.content.Context
import android.media.MediaRecorder
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
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
        Text("Capture a memory", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("Record a thought or choose an audio file. LifeLog will transcribe it and return the important details.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        ElevatedCard(shape = RoundedCornerShape(24.dp)) {
            Column(Modifier.padding(24.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(18.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Box(
                    Modifier
                        .size(96.dp)
                        .clip(CircleShape)
                        .background(
                            if (recording) Brush.linearGradient(listOf(Color(0xFFE53935), Color(0xFFFF7043)))
                            else Brush.linearGradient(listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.secondary))
                        ),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        if (recording) Icons.Default.Stop else Icons.Default.Mic,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(40.dp),
                    )
                }
                Button(
                    onClick = {
                        if (recording) {
                            recorder?.stop(); recorder?.release(); recorder = null; recording = false
                            recordingFile?.let { vm.uploadFile(it, "audio/mp4", onDone, onError) }
                        } else permission.launch(Manifest.permission.RECORD_AUDIO)
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(if (recording) "Stop and process" else "Record audio")
                }
                Button(
                    onClick = { picker.launch("audio/*") },
                    enabled = !recording && !state.uploading,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.Default.UploadFile, null)
                    Spacer(Modifier.size(8.dp))
                    Text("Choose audio file")
                }
                if (state.uploading) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                        Text("Transcribing and extracting your memory…")
                    }
                }
                state.lastUpload?.let { upload ->
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Memory saved", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
                        upload.extracted?.summary?.let { Text(it, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold) }
                        upload.transcript?.let { Text(it, maxLines = 6, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
        }
    }
}