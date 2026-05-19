"""Re-export registry helpers from merge_agent_discoveries."""
from merge_agent_discoveries import (
    BLOCKLIST, DATA, DISCOVERY_PATH, MIN_SUBS, OFF_TOPIC_USERNAMES, POSTS_DIR,
    REGISTRY_PATH, RESCRAPE_QUEUE_PATH, TGSTAT_SOURCES, USERNAME_ALIASES,
    classify_post_cache, dedupe_file_extensions, empty_registry_record,
    ingest_discovery_file, load_registry, merge_into_registry,
    normalize_discovery_entry, normalize_username, resolve_post_path,
    save_registry, sync_channel_seeds, sync_discovered_channels,
)
