import os
import select
import time
import errno
import redis
from .logger import Logger as log

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def write_to_pipe_with_timeout(pipe_path, message, timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            pipe_fd = os.open(pipe_path, os.O_WRONLY)
            try:
                os.set_blocking(pipe_fd, False)
                _, ready_to_write, _ = select.select([], [pipe_fd], [], timeout)
                if ready_to_write:
                    encoded_message = (message + '\n').encode('utf-8')
                    bytes_written = os.write(pipe_fd, encoded_message)
                    if bytes_written == len(encoded_message):
                        log.info(f"Wrote to pipe: {message}")
                        return True
                    log.warning(f"Partial write: {bytes_written}/{len(encoded_message)} bytes")
                else:
                    log.warning("Pipe not ready within timeout")
            finally:
                os.close(pipe_fd)
        except OSError as e:
            if e.errno in (errno.ENXIO, errno.EINTR):
                log.warning(f"Retrying: {str(e)}")
                time.sleep(0.1)
            else:
                log.error(f"Pipe error: {str(e)}")
                return False
    log.error("Pipe write failed after attempts")
    return False

def add_discord_role(guild_id, user_id, role_id):
    # Implement the Discord role addition logic here
    pass