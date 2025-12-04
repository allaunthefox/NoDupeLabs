# Plugin: startup_logger
# Logs startup and shutdown events

def on_startup(cfg):
    print(f"[plugins.startup_logger] startup event received; config keys: {len(cfg.keys())}")


def on_shutdown(reason: str, **kwargs):
    print(f"[plugins.startup_logger] shutdown event: {reason}")

# register hooks
pm.register("startup", on_startup)
pm.register("shutdown", on_shutdown)
