# Music Player (Spotify playlist)

Design playback for a music app: playlists, a "play next" queue, repeat and history.

## Requirements

1. `add_song(song_id)`; `create_playlist(name)`; `add_to_playlist(name, song_id)` appends
   (a song may appear more than once). Unknown song/playlist → `UnknownSong` /
   `UnknownPlaylist`; repeated playlist name → `DuplicatePlaylist`.
2. `play(name)` starts the playlist from its first entry and clears the queue and history
   (empty playlist → `EmptyPlaylist`). Returns the song now playing.
3. `enqueue(song_id)` adds a song to the play-next queue (FIFO). Needs something playing →
   `NothingPlaying`.
4. `next()` moves on and returns the new song: queued songs play first (the playlist
   position doesn't move); otherwise the next playlist entry. Past the last entry: with
   repeat `ALL` wrap to the first entry; with `NONE` playback stops and `next()` returns `""`.
5. `previous()` returns to the song played before the current one, restoring the playlist
   position too (no history → `NoHistory`). Songs left by `previous()` are not re-queued.
6. `set_repeat(mode)`; `current()` → the song playing (`NothingPlaying` when stopped).

## Things an interviewer will push on

- Where does "what plays next" live: player, playlist iterator, or a strategy?
- How would you add shuffle that doesn't repeat until all songs played?
- How do history and the queue interact?
