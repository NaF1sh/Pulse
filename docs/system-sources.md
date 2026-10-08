# Live music, volume, and pet reactions

`--observe` enables music and volume alongside notification mirroring by
default. Use --no-music / --no-volume to disable either adapter. Standalone
--music and --volume work without notification monitoring. Live flags cannot
be combined with --demo or history commands.

Music uses busctl JSON calls to discover org.mpris.MediaPlayer2.* services and
read org.mpris.MediaPlayer2.Player properties. Discovery and sampling run every
two seconds when the previous cycle finishes. Up to eight players are sampled
sequentially. A playing player wins over paused players; the previous player is
preferred when multiple players share that state. Title, artist, track ID or
playback-status changes update a persistent now-playing card while playing.
Music is held as a background view outside the notification queue, so all
temporary cards can interrupt it without priority tricks or starvation. On
timeout/dismissal of the final temporary card, the latest playing track returns.
Pause, stop, player disappearance or source disconnection clears the music view.
Single-clicking music does not dismiss it. Double-clicking music hides it for the current run without pausing
playback; double-click the idle pet or use Show music in the right-click panel
to restore the latest track. Hidden music stays hidden across track updates.
Notifications and volume still appear. Restarting resets this visibility toggle.
An initially paused player does not produce
a card. Position is not polled and no fake playback progress is displayed.
Metadata is rendered as bounded plain text. MPRIS artwork URLs support local
files and HTTP(S); QML loads supplied cover art asynchronously with a music-note
fallback. Absolute local artwork paths are converted to file URLs. When an image
is missing but xesam:url contains a valid YouTube watch, shorts, live, embed or
youtu.be link, Pulse uses the video's standard thumbnail. Spotify's supplied
HTTP(S) cover URLs work directly. A cover-bearing duplicate for the same playing
title is preferred over a bare browser entry, without switching to another song.
Other schemes and URLs containing credentials are rejected. The small
animated bars are a decorative playback indicator, not measured audio levels;
they stop while hidden and under reduced motion.

Volume uses `wpctl get-volume @DEFAULT_AUDIO_SINK@` every 500 ms. The first read
sets a baseline. Changes to volume or mute produce a 2.5-second card. Volume above
100% caps the meter while showing the actual percentage. Muted state shows a
zero meter and a Muted label. The redesigned level card is 58 px tall with a
speaker icon and a single meter; music is a 72 px horizontal card. No set-volume
or playback control commands run.
The default device is resolved by wpctl on every reading.

All commands use QProcess with a 1.5-second watchdog and an English locale for
stable parsing. Commands do not overlap within an adapter. Startup/read failures
report once and retry more slowly; source failures do not terminate Pulse.
Shutdown stops timers and subprocesses. Negative notification IDs separate
system cards from positive IDs assigned by the notification observer. System
cards use the same queue and rules but bypass notification-history recording.

The controller emits pet reactions only for eligible arrivals from idle and
manual dismissal of the last card. Replacement and queue changes do not trigger
new surprise reactions. QML shows surprise for 180 ms before expanding from idle,
then returns to the pet's normal expression. Happy persists through collapse
after dismissal. New arrivals cancel pending collapse. Reduced motion skips
reaction delays and temporary moods.

Automated checks cover real subprocess orchestration using fake system tools,
MPRIS metadata decoding and deduplication, player selection, volume/mute parsing,
amplification labels, error reporting, pet signals, and history exclusion.
Actual MPRIS/PipeWire access is blocked by this development environment; live
desktop music/volume display was confirmed by the user. The redesigned persistent
layout and new cover handling still need desktop acceptance. Test with a compatible player and normal desktop
volume keys while running ./run.sh --observe --debug.

References:

- [MPRIS Player interface](https://specifications.freedesktop.org/mpris/latest/Player_Interface.html)
- [WirePlumber command-line controls](https://pipewire.pages.freedesktop.org/wireplumber/tools/wpctl.html)
- [KDE browser integration and artwork](https://community.kde.org/Plasma/Browser_Integration)

Chrome may expose a playing title without art or a video URL. In KDE, the
official Plasma Integration extension can provide the richer MPRIS entry.
The native backend package and Chrome native-messaging manifest were verified
installed on this user's machine; extension enablement in Chrome was not checked.
Other users retain general MPRIS support. A browser that exposes no artwork/link
and has no integration helper gets a placeholder rather than guessed artwork.
Artwork from YouTube/Spotify is loaded only when the corresponding track supplies
an artwork URL or, for YouTube, a recognized video link; there is no title-search
service or Spotify account/API dependency.
