package com.lifelog.app.ui

import android.net.Uri
import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.navArgument
import com.lifelog.app.R
import com.lifelog.app.data.Api
import com.lifelog.app.data.EventSocket
import com.lifelog.app.data.LiveEvent
import com.lifelog.app.data.Memory
import com.lifelog.app.data.SearchResult
import com.lifelog.app.data.userMessage
import kotlinx.coroutines.launch

private data class Destination(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)
private val destinations = listOf(
    Destination("live", "Live", Icons.Default.GraphicEq),
    Destination("home", "Memories", Icons.Default.Home),
    Destination("search", "Search", Icons.Default.Search),
    Destination("settings", "Settings", Icons.Default.Settings),
)

@Composable
fun LifeLogApp(nav: NavHostController, vm: LifeLogViewModel = viewModel()) {
    val entry by nav.currentBackStackEntryAsState()
    val route = entry?.destination?.route ?: "live"
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val baseUrl by Api.baseUrlFlow.collectAsState()
    LaunchedEffect(baseUrl) { EventSocket.connect(baseUrl) }
    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                destinations.forEach { item ->
                    NavigationBarItem(
                        selected = route == item.route || route.startsWith(item.route),
                        onClick = { nav.navigate(item.route) { launchSingleTop = true; restoreState = true } },
                        icon = { Icon(item.icon, item.label) },
                        label = { Text(item.label) },
                    )
                }
            }
        },
        floatingActionButton = {
            if (route == "home") {
                FloatingActionButton(
                    onClick = { nav.navigate("capture") },
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                ) { Icon(Icons.Default.Add, "New memory") }
            }
        },
    ) { padding ->
        NavHost(nav, "live", Modifier.padding(padding)) {
            composable("live") { LiveScreen() }
            composable("home") { HomeScreen(vm, onError = { scope.launch { snackbar.showSnackbar(it) } }, onCapture = { nav.navigate("capture") }) }
            composable("search") { SearchScreen(vm) }
            composable("settings") { SettingsScreen(onError = { scope.launch { snackbar.showSnackbar(it) } }) }
            composable("capture") {
                CaptureScreen(
                    vm,
                    onDone = { vm.loadMemories(); nav.popBackStack() },
                    onError = { scope.launch { snackbar.showSnackbar(it) } },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen(vm: LifeLogViewModel, onError: (String) -> Unit, onCapture: () -> Unit) {
    LaunchedEffect(Unit) { vm.loadMemories() }
    val state by vm.state.collectAsState()
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        TopAppBar(
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Image(painterResource(R.drawable.ic_lifelog_logo), contentDescription = "LifeLog", modifier = Modifier.size(28.dp).clip(RoundedCornerShape(6.dp)))
                    Spacer(Modifier.width(10.dp))
                    Text("LifeLog", fontWeight = FontWeight.Bold)
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
        )
        Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(24.dp))
                    .background(Brush.linearGradient(listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.secondary)))
                    .padding(24.dp),
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Your moments, made useful.", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Color.White)
                    Text("A calm space for the things worth remembering.", style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.85f))
                    Spacer(Modifier.height(8.dp))
                    Text("${state.memories.size} memories stored", style = MaterialTheme.typography.labelLarge, color = Color.White.copy(alpha = 0.9f), fontWeight = FontWeight.SemiBold)
                }
            }
            Spacer(Modifier.height(20.dp))
            if (state.loading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            } else if (state.memories.isEmpty()) {
                EmptyState(onCapture)
            } else {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    items(state.memories, key = { it.id }) { memory ->
                        MemoryCard(memory, onDelete = { vm.delete(memory.id, onError) })
                    }
                    item { Spacer(Modifier.height(80.dp)) }
                }
            }
        }
    }
}

@Composable
private fun MemoryCard(memory: Memory, onDelete: () -> Unit) {
    ElevatedCard(shape = RoundedCornerShape(20.dp)) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top) {
                Column(Modifier.weight(1f)) {
                    Text(memory.date ?: "Recent memory", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(4.dp))
                    Text(memory.summary ?: memory.content.take(90), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, "Delete memory", tint = MaterialTheme.colorScheme.onSurfaceVariant) }
            }
            Text(memory.content, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 4, overflow = TextOverflow.Ellipsis)
            if (memory.tags.isNotEmpty()) {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    memory.tags.take(4).forEach { tag ->
                        AssistChip(onClick = {}, label = { Text(tag, style = MaterialTheme.typography.labelSmall) })
                    }
                }
            }
            if (memory.tasks.isNotEmpty() || memory.people.isNotEmpty()) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    if (memory.tasks.isNotEmpty()) Text("${memory.tasks.size} action${if (memory.tasks.size == 1) "" else "s"}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.secondary, fontWeight = FontWeight.SemiBold)
                    if (memory.people.isNotEmpty()) Text("${memory.people.size} people", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.tertiary, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

@Composable
private fun EmptyState(onCapture: () -> Unit) {
    Column(Modifier.fillMaxWidth().padding(top = 60.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Box(Modifier.size(88.dp).clip(CircleShape).background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
            Icon(Icons.Default.AutoAwesome, contentDescription = null, modifier = Modifier.size(40.dp), tint = MaterialTheme.colorScheme.primary)
        }
        Text("Nothing here yet", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text("Capture your first memory and let LifeLog do the rest.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(8.dp))
        Button(onClick = onCapture) {
            Icon(Icons.Default.Mic, null)
            Spacer(Modifier.width(8.dp))
            Text("Capture a memory")
        }
    }
}

@Composable
private fun SearchScreen(vm: LifeLogViewModel) {
    var query by remember { mutableStateOf("") }
    val results by vm.searchResults.collectAsState()
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Text("Find a moment", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("Search across everything you've captured.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            placeholder = { Text("Search your memories") },
            leadingIcon = { Icon(Icons.Default.Search, null) },
            trailingIcon = {
                TextButton(onClick = { vm.search(query) }) { Text("Search") }
            },
            shape = RoundedCornerShape(16.dp),
            singleLine = true,
        )
        if (results.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.Search, contentDescription = null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f))
                    Text("No results yet", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 20.dp)) {
                items(results) { result -> SearchCard(result) }
                item { Spacer(Modifier.height(80.dp)) }
            }
        }
    }
}

@Composable
private fun SearchCard(result: SearchResult) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(result.date ?: "Memory", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
            Text(result.summary ?: result.content, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text(result.content, maxLines = 3, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall, overflow = TextOverflow.Ellipsis)
            if (result.tags.isNotEmpty()) {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    result.tags.take(3).forEach { AssistChip(onClick = {}, label = { Text(it, style = MaterialTheme.typography.labelSmall) }) }
                }
            }
        }
    }
}

@Composable
private fun SettingsScreen(onError: (String) -> Unit) {
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Image(painterResource(R.drawable.ic_lifelog_logo), contentDescription = null, modifier = Modifier.size(40.dp).clip(RoundedCornerShape(10.dp)))
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text("LifeLog", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                        Text("Your memories, synced with the web.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Privacy", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                Text("Audio is sent to your LifeLog server for transcription. Extracted memories are stored by the server and displayed here. The website and app share the same data.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
            }
        }
        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("About", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                Text("LifeLog Android client v1.0", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                Text("ESP32 audio → server transcription → notes on app & web.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun LiveScreen() {
    val events by EventSocket.events.collectAsState()
    val connected by EventSocket.connected.collectAsState()
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Box(Modifier.size(10.dp).clip(CircleShape).background(if (connected) Color(0xFF4CAF50) else Color(0xFFE53935)))
            Text(if (connected) "Connected to server events" else "Connecting…", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        }
        Text("Live transcripts from your ESP32 audio stream.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
        if (events.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    CircularProgressIndicator()
                    Text("Waiting for transcript messages…", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(events, key = { it.id }) { event ->
                    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date(event.receivedAt)), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                            Text(event.text, style = MaterialTheme.typography.bodyMedium)
                            if (event.raw != event.text) {
                                Text(event.raw, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 3, overflow = TextOverflow.Ellipsis)
                            }
                        }
                    }
                }
                item { Spacer(Modifier.height(80.dp)) }
            }
        }
    }
}