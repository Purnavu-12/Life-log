package com.lifelog.app.ui

import android.net.Uri
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.combinedClickable
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
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.WbSunny
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
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
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import com.lifelog.app.R
import com.lifelog.app.data.ActionItem
import com.lifelog.app.data.Api
import com.lifelog.app.data.CalendarEvent
import com.lifelog.app.data.EventSocket
import com.lifelog.app.data.GoogleState
import com.lifelog.app.data.GmailMessage
import com.lifelog.app.data.LiveEvent
import com.lifelog.app.data.Memory
import com.lifelog.app.data.SearchResult
import kotlinx.coroutines.launch

private data class Destination(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)

private val destinations = listOf(
    Destination("today", "Today", Icons.Default.WbSunny),
    Destination("home", "Memories", Icons.Default.Home),
    Destination("chat", "Chat", Icons.Default.Chat),
    Destination("live", "Live", Icons.Default.GraphicEq),
    Destination("settings", "Settings", Icons.Default.Settings),
)

@Composable
fun LifeLogApp(nav: NavHostController, vm: LifeLogViewModel = viewModel()) {
    val entry by nav.currentBackStackEntryAsState()
    val route = entry?.destination?.route ?: "today"
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
        NavHost(nav, "today", Modifier.padding(padding)) {
            composable("today") { TodayScreen(vm) }
            composable("home") {
                HomeScreen(
                    vm,
                    onError = { scope.launch { snackbar.showSnackbar(it) } },
                    onCapture = { nav.navigate("capture") },
                    onSearch = { nav.navigate("search") },
                )
            }
            composable("search") { SearchScreen(vm) }
            composable("chat") { ChatScreen(vm) }
            composable("live") { LiveScreen(vm) }
            composable("settings") { SettingsScreen(vm, onError = { scope.launch { snackbar.showSnackbar(it) } }) }
            composable("capture") {
                CaptureScreen(
                    vm,
                    onDone = { vm.loadMemories(); vm.loadBriefing(); nav.popBackStack() },
                    onError = { scope.launch { snackbar.showSnackbar(it) } },
                )
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Today
// ---------------------------------------------------------------------------

@Composable
private fun TodayScreen(vm: LifeLogViewModel) {
    val state by vm.state.collectAsState()
    LaunchedEffect(Unit) {
        vm.loadBriefing()
        vm.loadGoogleStatus()
        vm.loadActions()
    }
    val briefing = state.briefing
    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Image(
                painterResource(R.drawable.ic_lifelog_logo),
                contentDescription = null,
                modifier = Modifier.size(28.dp).clip(RoundedCornerShape(6.dp)),
            )
            Spacer(Modifier.width(10.dp))
            Text("Today", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        }
        if (state.briefingLoading && briefing == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            return@Column
        }
        if (briefing == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Could not load your briefing.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    TextButton(onClick = { vm.loadBriefing() }) { Text("Retry") }
                }
            }
            return@Column
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    StatCard("Memories", briefing.totalMemories.toString(), Modifier.weight(1f))
                    StatCard("Actions", briefing.pendingActions.toString(), Modifier.weight(1f))
                }
            }
            if (briefing.calendar.isNotEmpty()) {
                item { SectionTitle("Calendar") }
                itemsIndexed(briefing.calendar) { _, event -> EventCard(event) }
            }
            if (briefing.importantEmails.isNotEmpty()) {
                item { SectionTitle("Important emails") }
                itemsIndexed(briefing.importantEmails) { _, mail -> MailCard(mail) }
            }
            if (briefing.actions.isNotEmpty()) {
                item { SectionTitle("Actions") }
                itemsIndexed(briefing.actions) { _, action -> ActionCard(action) }
            }
            if (briefing.memories.isNotEmpty()) {
                item { SectionTitle("Recent memories") }
                itemsIndexed(briefing.memories) { _, memory -> BriefingMemoryCard(memory) }
            }
            item { Spacer(Modifier.height(80.dp)) }
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
}

@Composable
private fun StatCard(label: String, value: String, modifier: Modifier = Modifier) {
    ElevatedCard(shape = RoundedCornerShape(18.dp), modifier = modifier) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun EventCard(event: CalendarEvent) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(event.summary.ifBlank { "Event" }, fontWeight = FontWeight.SemiBold)
            event.start?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
            event.location?.takeIf { it.isNotBlank() }?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
            }
        }
    }
}

@Composable
private fun MailCard(mail: GmailMessage) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(mail.subject.ifBlank { "Email" }, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (mail.sender.isNotBlank()) {
                Text(mail.sender, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            if (mail.snippet.isNotBlank()) {
                Text(mail.snippet, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

@Composable
private fun ActionCard(action: ActionItem) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Icon(Icons.Default.AutoAwesome, null, tint = MaterialTheme.colorScheme.primary)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(action.title.ifBlank { "Action" }, fontWeight = FontWeight.SemiBold)
                action.description?.takeIf { it.isNotBlank() }?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 2, overflow = TextOverflow.Ellipsis)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    action.priority?.takeIf { it.isNotBlank() }?.let {
                        AssistChip(onClick = {}, label = { Text(it, style = MaterialTheme.typography.labelSmall) })
                    }
                    action.status?.takeIf { it.isNotBlank() }?.let {
                        AssistChip(onClick = {}, label = { Text(it, style = MaterialTheme.typography.labelSmall) })
                    }
                }
            }
        }
    }
}

@Composable
private fun BriefingMemoryCard(memory: Memory) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(memory.title.ifBlank { "Memory" }, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (memory.transcript.isNotBlank()) {
                Text(memory.transcript, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 3, overflow = TextOverflow.Ellipsis)
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Memories
// ---------------------------------------------------------------------------

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen(vm: LifeLogViewModel, onError: (String) -> Unit, onCapture: () -> Unit, onSearch: () -> Unit) {
    LaunchedEffect(Unit) {
        vm.loadMemories()
        vm.loadGoogleStatus()
    }
    val state by vm.state.collectAsState()
    LaunchedEffect(state.googleStatus?.connected) {
        if (state.googleStatus?.connected == true) {
            vm.loadUpcomingEvents()
            vm.loadImportantEmails()
        }
    }
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        TopAppBar(
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Image(
                        painterResource(R.drawable.ic_lifelog_logo),
                        contentDescription = "LifeLog",
                        modifier = Modifier.size(28.dp).clip(RoundedCornerShape(6.dp)),
                    )
                    Spacer(Modifier.width(10.dp))
                    Text("LifeLog", fontWeight = FontWeight.Bold)
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            actions = { IconButton(onClick = onSearch) { Icon(Icons.Default.Search, "Search memories") } },
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
                    if (state.upcomingEvents.isNotEmpty()) {
                        item { SectionTitle("Upcoming events") }
                        itemsIndexed(state.upcomingEvents.take(3)) { _, event -> EventCard(event) }
                        item { Spacer(Modifier.height(4.dp)) }
                    }
                    if (state.importantEmails.isNotEmpty()) {
                        item { SectionTitle("Important emails") }
                        itemsIndexed(state.importantEmails.take(3)) { _, mail -> MailCard(mail) }
                        item { Spacer(Modifier.height(4.dp)) }
                    }
                    itemsIndexed(state.memories) { _, memory ->
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
                    Text(memory.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
                }
                IconButton(onClick = onDelete) { Icon(Icons.Default.Delete, "Delete memory", tint = MaterialTheme.colorScheme.onSurfaceVariant) }
            }
            if (memory.transcript.isNotBlank()) {
                Text(memory.transcript, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 4, overflow = TextOverflow.Ellipsis)
            }
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
    Column(
        Modifier.fillMaxWidth().padding(top = 60.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
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

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

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
            trailingIcon = { TextButton(onClick = { vm.search(query) }) { Text("Search") } },
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
            result.date?.let {
                Text(it, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
            }
            Text(result.summary ?: result.text, fontWeight = FontWeight.SemiBold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (result.text.isNotBlank() && result.text != result.summary) {
                Text(result.text, maxLines = 3, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall, overflow = TextOverflow.Ellipsis)
            }
            if (result.tags.isNotEmpty()) {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    result.tags.take(3).forEach { AssistChip(onClick = {}, label = { Text(it, style = MaterialTheme.typography.labelSmall) }) }
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

@Composable
private fun ChatScreen(vm: LifeLogViewModel) {
    val state by vm.state.collectAsState()
    var input by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(state.chatMessages.size) {
        if (state.chatMessages.isNotEmpty()) listState.animateScrollToItem(state.chatMessages.size - 1)
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Neural Core", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text("Ask anything about your memories.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
            }
            if (state.chatMessages.isNotEmpty()) {
                TextButton(onClick = { vm.clearChat() }) { Text("Clear") }
            }
        }
        Spacer(Modifier.height(12.dp))
        if (state.chatMessages.isEmpty()) {
            Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.Chat, contentDescription = null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.primary)
                    Text("Start a conversation", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        } else {
            LazyColumn(state = listState, modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.chatMessages) { message ->
                    val isUser = message.role == "user"
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start) {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = if (isUser) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                            ),
                            modifier = Modifier.fillMaxWidth(0.88f),
                        ) {
                            Text(
                                message.content,
                                modifier = Modifier.padding(14.dp),
                                color = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface,
                            )
                        }
                    }
                }
                if (state.chatLoading) {
                    item {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            Text("Thinking…", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
                if (state.chatSources.isNotEmpty() && !state.chatLoading) {
                    item {
                        HorizontalDivider(Modifier.padding(vertical = 8.dp))
                        Text("Sources", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    items(state.chatSources) { source ->
                        Text(
                            "• ${source.text.take(140)}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Ask about your memories…") },
                shape = RoundedCornerShape(16.dp),
                maxLines = 4,
            )
            IconButton(
                onClick = { vm.sendChat(input); input = "" },
                enabled = input.isNotBlank() && !state.chatLoading,
            ) { Icon(Icons.Default.Send, "Send") }
        }
    }
}

// ---------------------------------------------------------------------------
// Live
// ---------------------------------------------------------------------------

@Composable
private fun LiveScreen(vm: LifeLogViewModel) {
    val events by EventSocket.events.collectAsState()
    val connected by EventSocket.connected.collectAsState()
    val state by vm.state.collectAsState()

    LaunchedEffect(Unit) { vm.loadServerStatus() }
    LaunchedEffect(events.size) { if (events.isNotEmpty()) vm.loadServerStatus() }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(10.dp).clip(CircleShape).background(if (connected) Color(0xFF4CAF50) else Color(0xFFE53935)))
            Spacer(Modifier.width(10.dp))
            Text("Live", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        }
        Text(
            if (connected) "Connected to the server event stream." else "Connecting to the server event stream…",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            style = MaterialTheme.typography.bodySmall,
        )
        state.serverStatus?.let { status ->
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatusPill("${status.connectedDevices} device")
                StatusPill(if (status.recording) "Recording" else "Idle")
                StatusPill("${status.queueSize} queued")
            }
        }
        Spacer(Modifier.height(12.dp))
        if (events.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    CircularProgressIndicator()
                    Text("Waiting for transcript messages…", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(events, key = { it.id }) { event -> LiveEventCard(event) }
                item { Spacer(Modifier.height(80.dp)) }
            }
        }
    }
}

@Composable
private fun StatusPill(text: String) {
    AssistChip(onClick = {}, label = { Text(text, style = MaterialTheme.typography.labelSmall) })
}

@Composable
private fun LiveEventCard(event: LiveEvent) {
    if (event.isStatus) {
        ElevatedCard(shape = RoundedCornerShape(14.dp)) {
            Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Icon(Icons.Default.GraphicEq, null, tint = MaterialTheme.colorScheme.secondary, modifier = Modifier.size(18.dp))
                Text(event.text, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    } else {
        ElevatedCard(shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(
                        java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault())
                            .format(java.util.Date(event.receivedAt)),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                    event.sequence?.let {
                        Text("#$it", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                Text(event.text, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun SettingsScreen(vm: LifeLogViewModel, onError: (String) -> Unit) {
    val state by vm.state.collectAsState()
    val context = androidx.compose.ui.platform.LocalContext.current
    val connectedEvent by GoogleState.connectedEvent.collectAsState()
    var showDeveloper by remember { mutableStateOf(false) }

    val refreshTrigger by GoogleState.refreshTrigger.collectAsState()

    LaunchedEffect(Unit) { vm.loadGoogleStatus() }
    LaunchedEffect(connectedEvent) {
        if (connectedEvent != null) {
            vm.loadGoogleStatus()
            vm.loadUpcomingEvents()
            vm.loadImportantEmails()
            GoogleState.consume()
        }
    }
    // Returning from the Google sign-in tab: re-check the connection status.
    LaunchedEffect(refreshTrigger) {
        if (refreshTrigger > 0) {
            vm.loadGoogleStatus()
            vm.loadUpcomingEvents()
            vm.loadImportantEmails()
        }
    }

    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Text("Settings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)

        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(20.dp)
                    .combinedClickable(
                        onClick = { showDeveloper = !showDeveloper },
                    ),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Image(
                    painterResource(R.drawable.ic_lifelog_logo),
                    contentDescription = null,
                    modifier = Modifier.size(40.dp).clip(RoundedCornerShape(10.dp)),
                )
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("LifeLog", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                    Text("Your memories, synced with the web.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Google account", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                val status = state.googleStatus
                if (status?.connected == true) {
                    Text("Connected: ${status.email ?: "Google account"}", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall)
                    Button(onClick = { vm.disconnectGoogle(onError = onError) }) { Text("Disconnect Google") }
                } else {
                    Text("Connect Google to see calendar events and important emails.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                    Button(onClick = {
                        androidx.browser.customtabs.CustomTabsIntent.Builder()
                            .build()
                            .launchUrl(context, Uri.parse(Api.googleAuthUrl()))
                    }) { Text("Connect Google") }
                }
            }
        }

        if (showDeveloper) {
            DeveloperPanel()
        }

        ElevatedCard(shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Privacy", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
                Text(
                    "Audio is sent to your LifeLog server for transcription. Extracted memories are stored by the server and displayed here. The website and app share the same data.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodySmall,
                )
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
private fun DeveloperPanel() {
    var url by remember { mutableStateOf(Api.baseUrlFlow.value) }
    var message by remember { mutableStateOf<String?>(null) }
    ElevatedCard(shape = RoundedCornerShape(20.dp)) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Developer", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("Server URL") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(14.dp),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = {
                    Api.setBaseUrl(url)
                    message = "Saved."
                }) { Text("Save") }
                TextButton(onClick = {
                    Api.setBaseUrl(Api.baseUrlFlow.value)
                    message = "Reset to default."
                }) { Text("Reset") }
            }
            message?.let { Text(it, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall) }
        }
    }
}
