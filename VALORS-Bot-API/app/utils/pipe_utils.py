import os
import select
import time
import errno

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
                        return True
            finally:
                os.close(pipe_fd)
        except OSError as e:
            if e.errno in (errno.ENXIO, errno.EINTR):
                time.sleep(0.1)
            else:
                return False
    return False