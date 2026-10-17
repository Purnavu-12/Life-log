package com.lifelog.app.ui

import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.navArgument
import androidx.navigation.NavType
import com.lifelog.app.data.Memory
import com.lifelog.app.data.SearchResult
import com.lifelog.app.data.userMessage
import kotlinx.coroutines.launch

private data class Destination(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)
private val destinations = listOf(
    Destination("home", "Memories", Icons.Default.Home),
    Destination("search", "Search", Icons.Default.Search),
    Destination("settings", "Settings", Icons.Default.Settings),
)

@Composable
fun LifeLogApp(nav: NavHostController, vm: LifeLogViewModel = viewModel()) {
    val entry by nav.currentBackStackEntryAsState()
    val route = entry?.destination?.route ?: "home"
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            NavigationBar {
                destinations.forEach { item ->
                    NavigationBarItem(
                        selected = route == item.route,
                        onClick = { nav.navigate(item.route) { launchSingleTop = true } },
                        icon = { Icon(item.icon, item.label) },
                        label = { Text(item.label) },
                    )
                }
            }
        },
        floatingActionButton = {
            if (route == "home") FloatingActionButton(onClick = { nav.navigate("capture") }) {
                Icon(Icons.Default.Add, "New memory")
            }
        },
    ) { padding ->
        NavHost(nav, "home", Modifier.padding(padding)) {
            composable("home") { HomeScreen(vm, onError = { scope.launch { snackbar.showSnackbar(it) } }) }
            composable("search") { SearchScreen(vm) }
            composable("settings") { SettingsScreen() }
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
private fun HomeScreen(vm: LifeLogViewModel, onError: (String) -> Unit) {
    LaunchedEffect(Unit) { vm.loadMemories() }
    val state by vm.state.collectAsState()
    Scaffold(topBar = { TopAppBar(title = { Text("LifeLog", fontWeight = FontWeight.Bold) }) }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(horizontal = 20.dp)) {
            Text("Your moments, made useful.", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("A calm space for the things worth remembering.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (state.loading) CircularProgressIndicator(Modifier.padding(top = 40.dp))
            else if (state.memories.isEmpty()) EmptyState()
            else LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 24.dp)) {
                items(state.memories, key = { it.id }) { memory ->
                    MemoryCard(memory, onDelete = { vm.delete(memory.id, onError) })
                }
            }
        }
    }
}

@Composable
private fun MemoryCard(memory: Memory, onDelete: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(Modifier.weight(1f)) {
                    Text(memory.date ?: "Recent memory", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                    Text(memory.summary ?: memory.content.take(100), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, "Delete memory") }
            }
            Text(memory.content, style = MaterialTheme.typography.bodyMedium, maxLines = 5)
            if (memory.tags.isNotEmpty()) Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                memory.tags.take(4).forEach { AssistChip(onClick = {}, label = { Text(it) }) }
            }
            if (memory.tasks.isNotEmpty()) Text("${memory.tasks.size} action${if (memory.tasks.size == 1) "" else "s"} captured", color = MaterialTheme.colorScheme.secondary)
        }
    }
}

@Composable
private fun EmptyState() {
    Column(Modifier.fillMaxWidth().padding(top = 80.dp), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
        Text("Nothing here yet", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text("Tap + to capture your first memory.", color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun SearchScreen(vm: LifeLogViewModel) {
    var query by remember { mutableStateOf("") }
    val results by vm.searchResults.collectAsState()
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Text("Find a moment", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth().padding(top = 16.dp), placeholder = { Text("Search your memories") }, trailingIcon = {
            IconButton(onClick = { vm.search(query) }) { Icon(Icons.Default.Search, "Search") }
        })
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 20.dp)) {
            items(results) { result -> SearchCard(result) }
        }
    }
}

@Composable
private fun SearchCard(result: SearchResult) {
    Card { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(result.date ?: "Memory", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelLarge)
        Text(result.summary ?: result.content, fontWeight = FontWeight.SemiBold)
        Text(result.content, maxLines = 3, color = MaterialTheme.colorScheme.onSurfaceVariant)
    } }
}

@Composable
private fun SettingsScreen() {
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Card { Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("LifeLog server", fontWeight = FontWeight.SemiBold)
            Text("The app uses the same transcription and extraction service as the website.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        } }
        Text("Privacy", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Text("Audio is sent to your configured LifeLog server for transcription. Extracted memories are stored by the server and displayed here.", color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
